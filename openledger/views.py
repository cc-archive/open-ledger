from flask import Flask, render_template, request

from openledger import app, forms, licenses

from openledger.handlers.handler_500px import photos as search_500
from openledger.handlers.handler_rijks import photos as search_rijks
from openledger.handlers.handler_flickr import photos as search_flickr
from openledger.handlers.handler_wikimedia import photos as search_wikimedia

PER_PAGE = 20

search_funcs = {
    "fpx": search_500,
    "flickr": search_flickr,
    "rijks": search_rijks,
    "wikimedia": search_wikimedia,
}

@app.route("/")
def index(provider=None):
    form = forms.SearchForm()
    search = request.args.get('search')
    page = request.args.get('page') or 1
    per_page = request.args.get('per_page') or PER_PAGE
    user_licenses = request.args.getlist('licenses') or ["ALL"]
    providers = search_funcs.keys() if not provider else [provider]
    results = {}

    if search:
        for p in providers:
            results[p] = search_funcs[p](search=search, licenses=user_licenses, page=page, per_page=per_page)
    return render_template('index.html', results=results, form=form,
                           user_licenses=user_licenses,
                           search=search,
                           license_map=licenses.license_map_from_partners())

@app.route("/provider/<provider>")
def by_provider(provider):
    return index(provider=provider)

@app.template_filter('pluralize')
def pluralize(number, singular='', plural='s'):
    try:
        number = int(number)
    except ValueError:
        number = 0
    finally:
        return singular if number == 1 else plural
