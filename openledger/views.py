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

@app.route("/image/external/")
def by_image():
    """Load an image from an external provider, where values will be passed by query string"""
    url = request.args.get('url')
    provider_url = request.args.get('provider_url')
    title = request.args.get('title')
    license = request.args.get('license')
    creator = request.args.get('creator')
    return render_template('image-external.html',
                           url=url,
                           title=title,
                           provider_url=provider_url,
                           license=license,
                           creator=creator)




@app.route("/source/openimages")
def openimages():
    """Images sourced from Google's OpenImage project"""
    results = []
    form, search_data = init_search()

    if search_data['search']:
        terms = search_data['search'].split(' ')
        results = Image.query.distinct().join('tags').filter(
            and_(
                *[
                    or_(
                        Image.title.contains(s),
                        Tag.tag.contains(s),
                    ) for s in terms
                ]
              )
            ).paginate(page=search_data['page'],
                       per_page=search_data['per_page'],
                       error_out=False)
    return render_template('openimages.html',
                           results=results,
                           form=form,
                           search_data=search_data,)

def init_search(provider=None):
    """Set up common search initialization; returns a tuple"""
    results = {}
    form = forms.SearchForm()
    search = request.args.get('search')
    if search:
        search = search.lower().strip()
    user_licenses = request.args.getlist('licenses') or ["ALL"]

    # Prepopulate the user's search data in the form
    form.search.process_data(search)
    form.licenses.process_data(user_licenses)

    search_data = {'search': search,
                   'page': request.args.get('page') or 1,
                   'per_page': request.args.get('per_page') or PER_PAGE,
                   'providers': search_funcs.keys() if not provider else [provider],
                   'licenses': user_licenses}

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
