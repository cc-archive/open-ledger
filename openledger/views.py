from flask import Flask, render_template, request

from openledger import app, forms, util

from openledger.handlers.handler_500px import photos as search_500
from openledger.handlers.handler_rijks import photos as search_rijks
from openledger.handlers.handler_flickr import photos as search_flickr
from openledger.handlers.handler_wikimedia import photos as search_wikimedia

@app.route("/")
def index():

    search = request.args.get('search')
    form = forms.SearchForm()
    results = {}
    if search:
        results['wikimedia'] = search_wikimedia(search=search)
        results['fpx'] = search_500(search=search)
        results['rijks'] = search_rijks(search=search)
        results['flickr'] = search_flickr(search=search)
    return render_template('index.html', results=results, form=form,
                           search=search, licenses=util.licenses())
