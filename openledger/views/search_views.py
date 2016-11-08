import logging

from elasticsearch_dsl import Search, Q
from flask import Flask, render_template, request, abort
from sqlalchemy import and_, or_, not_, distinct

from openledger import app, forms, licenses, search
from openledger.handlers.handler_500px import photos as search_500
from openledger.handlers.handler_rijks import photos as search_rijks
from openledger.handlers.handler_flickr import photos as search_flickr
from openledger.handlers.handler_wikimedia import photos as search_wikimedia
from openledger.models import db, Image, Tag

PER_PAGE = 20

# Search by source
WORK_TYPES = {
    'photos': ['flickr'],
    'cultural': ['rijksmuseum']
}

search_funcs = {
    "fpx": search_500,
    "flickr": search_flickr,
    "rijks": search_rijks,
    "wikimedia": search_wikimedia,
}

log = logging.getLogger(__name__)
console = logging.StreamHandler()
log.addHandler(console)
log.setLevel(logging.INFO)

@app.route('/')
def fulltext():
    """Primary search interface of the Open Ledger collection"""
    s = Search()

    form, search_data = init_search()

    results = search.Results(page=search_data['page'])

    if search_data['search']:
        and_queries = []
        or_queries = []

        # Search fields
        if 'title' in search_data.get('search_fields'):
            or_queries.append(Q("match", title=search_data['search']))
        if 'tags' in search_data.get('search_fields'):
            or_queries.append(Q("match", tags=search_data['search']))
        if 'creator' in search_data.get('search_fields'):
            or_queries.append(Q("match", creator=search_data['search']))

        # Work types must match
        if 'photos' in search_data.get('work_types'):
            and_queries.append(Q("match", source=WORK_TYPES['photos'][0]))  # FIXME make this an OR
        if 'cultural' in search_data.get('work_types'):
            and_queries.append(Q("match", source=WORK_TYPES['cultural'][0]))

        q = Q('bool',
              should=or_queries,
              must=Q('bool', should=and_queries, minimum_should_match=1),
              minimum_should_match=1)

        s = s.query(q)
        response = s.execute()
        results.pages = int(int(response.hits.total) / PER_PAGE)
        start = results.page
        end = start + PER_PAGE
        for r in s[start -1:end]:
            results.items.append(r)

    search_data_for_pagination = {i: search_data[i] for i in search_data if i != 'page'}

    return render_template('results.html',
                           results=results,
                           form=form,
                           search_data=search_data,
                           search_data_for_pagination=search_data_for_pagination)

@app.route("/provider-apis")
def provider_apis(provider=None):
    """Search by passing queries through to provider apis"""
    results = {}
    form, search_data = init_search(provider)

    if search_data['search']:
        for p in search_data['providers']:
            results[p] = search_funcs[p](search=search_data['search'],
                                         licenses=search_data['licenses'],
                                         page=search_data['page'],
                                         per_page=search_data['per_page'])
    return render_template('provider-results.html',
                           results=results,
                           form=form,
                           search_data=search_data,
                           license_map=licenses.license_map_from_partners())

@app.route("/provider/<provider>")
def by_provider(provider):
    return provider_apis(provider=provider)

@app.route("/image/detail/")
def by_image():
    """Load an image in detail view, passing parameters by query string so that
    we can either load an image from an external provider or from our own datastore."""
    url = request.args.get('url')
    provider_url = request.args.get('provider_url')
    title = request.args.get('title')
    license = request.args.get('license')
    creator = request.args.get('creator')
    provider = request.args.get('provider')
    creator_url = request.args.get('creator_url')
    license_version = licenses.license_map_from_partners()[provider]['version']
    license_url = licenses.get_license_url(license, license_version)
    return render_template('detail.html',
                           image=None,
                           url=url,
                           title=title,
                           provider_url=provider_url,
                           license=license,
                           license_url=license_url,
                           license_version=license_version,
                           creator=creator,
                           creator_url=creator_url)

@app.route ("/ledger/detail/<path:identifier>")
def detail(identifier):
    """Get a detailed representation of an item in the ledger"""
    image = Image.query.filter_by(identifier=identifier).first()
    if not image:
        abort(404)
    url = image.url
    provider_url = image.foreign_landing_url
    title = image.title
    provider = image.provider
    license_version = image.license_version
    license = image.license
    license_url = licenses.get_license_url(license, license_version)
    creator = image.creator
    creator_url = image.creator_url
    return render_template('detail.html',
                           image=image,
                           url=url,
                           title=title,
                           provider_url=provider_url,
                           license=license,
                           license_url=license_url,
                           license_version=license_version,
                           creator=creator,
                           creator_url=creator_url)




def init_search(provider=None):
    """Set up common search initialization; returns a tuple of the initialized
    search form and the search data extracted from the user's query or defaults.
    """
    results = {}
    form = forms.SearchForm()
    search = request.args.get('search')
    search = search.lower().strip() if search else None

    user_licenses = request.args.getlist('licenses') or [licenses.DEFAULT_LICENSE]
    search_fields = request.args.getlist('search_fields') or forms.FIELD_DEFAULT
    work_types = request.args.getlist('work_types') or forms.WORK_TYPE_DEFAULT

    # Ensure that all the licenses evaluate to something
    for i, l in enumerate(user_licenses):
        user_licenses[i] = l.upper()
        if user_licenses[i] not in licenses.LICENSE_LIST:
            log.warn("Got an unknown license %s, setting to default %s", l, licenses.DEFAULT_LICENSE)
            user_licenses[i] = licenses.DEFAULT_LICENSE

    # Prepopulate the user's search data in the form
    form.search.process_data(search)
    form.licenses.process_data(user_licenses)
    form.search_fields.process_data(search_fields)
    form.work_types.process_data(work_types)

    search_data = {'search': search,
                   'page': request.args.get('page') or 1,
                   'per_page': request.args.get('per_page') or PER_PAGE,
                   'providers': search_funcs.keys() if not provider else [provider],
                   'licenses': user_licenses,
                   'search_fields': search_fields,
                   'work_types': work_types}

    search_data['page'] = int(search_data['page'])
    search_data['per_page'] = int(search_data['per_page'])

    return (form, search_data)

@app.template_filter('pluralize')
def pluralize(number, singular='', plural='s'):
    try:
        number = int(number)
    except ValueError:
        number = 0
    finally:
        return singular if number == 1 else plural
