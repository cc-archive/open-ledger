import logging

from flask import Flask, render_template, request
from sqlalchemy import and_, or_, not_, distinct

from openledger import app, forms, licenses
from openledger.handlers.handler_500px import photos as search_500
from openledger.handlers.handler_rijks import photos as search_rijks
from openledger.handlers.handler_flickr import photos as search_flickr
from openledger.handlers.handler_wikimedia import photos as search_wikimedia
from openledger.models import db, Image, Tag

PER_PAGE = 20

search_funcs = {
    "fpx": search_500,
    "flickr": search_flickr,
    "rijks": search_rijks,
    "wikimedia": search_wikimedia,
}

log = logging.getLogger(__name__)

@app.route("/")
def index(provider=None):
    """Primary entry point for the search page"""
    results = {}
    form, search_data = init_search(provider)

    if search_data['search']:
        for p in search_data['providers']:
            results[p] = search_funcs[p](search=search_data['search'],
                                         licenses=search_data['licenses'],
                                         page=search_data['page'],
                                         per_page=search_data['per_page'])
    return render_template('index.html',
                           results=results,
                           form=form,
                           search_data=search_data,
                           license_map=licenses.license_map_from_partners())

@app.route("/provider/<provider>")
def by_provider(provider):
    return index(provider=provider)

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
    license_version = licenses.license_map_from_partners()[provider]['version']
    license_url = licenses.get_license_url(license, license_version)
    return render_template('detail.html',
                           url=url,
                           title=title,
                           provider_url=provider_url,
                           license=license,
                           license_url=license_url,
                           creator=creator)

@app.route ("/ledger/detail/<identifier>")
def detail(identifier):
    """Get a detailed representation of an item in the ledger"""
    image = Image.query.filter_by(identifier=identifier).first()
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
                           creator=creator,
                           creator_url=creator_url)

@app.route("/source/openimages")
def openimages():
    """Search a local database of images sourced from Google's OpenImage project"""
    results = []
    form, search_data = init_search()
    # For each search term, check in both the image title field and linked Tags
    if search_data['search']:
        terms = search_data['search'].split(' ')

        # If we're searching tags, we need a join; otherwise nope
        if 'tags' in search_data.get('search_fields'):
            filter_query = Image.query.distinct().join('tags').filter
        else:
            filter_query = Image.query.distinct().filter

        results = filter_query(
            and_(
                *[
                    or_(
                        Image.creator.ilike(s) if 'creator' in search_data.get('search_fields') else None,
                        Image.title.contains(s) if 'title' in search_data.get('search_fields') else None,
                        Tag.name == s if 'tags' in search_data.get('search_fields') else None,
                    ) for s in terms
                ]
              )
            ).paginate(page=search_data['page'],
                       per_page=search_data['per_page'],
                       error_out=False)

    # Search data with fields we want to override in pagination removed
    search_data_for_pagination = {i:search_data[i] for i in search_data if i != 'page'}
    return render_template('openimages.html',
                           results=results,
                           form=form,
                           search_data=search_data,
                           search_data_for_pagination=search_data_for_pagination)

def init_search(provider=None):
    """Set up common search initialization; returns a tuple of the initialized
    search form and the search data extracted from the user's query or defaults.
    """
    results = {}
    form = forms.SearchForm()
    search = request.args.get('search')
    search = search.lower().strip() if search else None

    user_licenses = request.args.getlist('licenses') or [licenses.DEFAULT_LICENSE]
    search_fields = request.args.getlist('search_fields')

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

    search_data = {'search': search,
                   'page': request.args.get('page') or 1,
                   'per_page': request.args.get('per_page') or PER_PAGE,
                   'providers': search_funcs.keys() if not provider else [provider],
                   'licenses': user_licenses,
                   'search_fields': search_fields}

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
