from flask import Flask, render_template, request

import forms

app = Flask(__name__, instance_relative_config=True)
app.config.from_pyfile('config.py')

@app.route("/")
def index():
    from handlers.handler_500px import photos as search_500, LICENSE_LOOKUP
    from handlers.handler_rijks import photos as search_rijks

    search = request.args.get('search')
    form = forms.SearchForm()
    results = {}
    if search:
        results['fpx'] = search_500(search=search)
        results['rijks'] = search_rijks(search=search)
    return render_template('index.html', results=results, form=form, search=search, licenses=LICENSE_LOOKUP)

if __name__ == '__main__':
    # Run me as 'python -m app' to avoid path/import problems
    app.run()
