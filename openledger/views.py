from flask import Flask, render_template, request

from openledger import app, forms, util

from openledger.handlers.handler_500px import photos as search_500
from openledger.handlers.handler_rijks import photos as search_rijks
from openledger.handlers.handler_flickr import photos as search_flickr
from openledger.handlers.handler_wikimedia import photos as search_wikimedia

@app.route("/")
def index():
    form = forms.SearchForm()
    search = request.args.get('search')
    licenses = request.args.getlist('licenses') or ["ALL-CC"]
    results = {}

    if search:
        results['flickr'] = search_flickr(search=search, licenses=licenses)
        results['fpx'] = search_500(search=search, licenses=licenses)
        results['wikimedia'] = search_wikimedia(search=search)
        results['rijks'] = search_rijks(search=search)
        results['wikimedia'] = search_wikimedia(search=search)
    return render_template('index.html', results=results, form=form,
                           user_licenses=licenses,
                           search=search, licenses=util.licenses())
