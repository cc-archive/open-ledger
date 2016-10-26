from flask import Flask
from elasticsearch_dsl.connections import connections
from flask_assets import Environment, Bundle

application = Flask(__name__)
app = application  # Workaround for AWS-specific configuration
app.config.from_pyfile('default_settings.py')

assets = Environment(app)
if not app.debug:
    assets.manifest = 'file'
    assets.manifest = 'file:/tmp/openledger.assets'  # explict filename

js = Bundle('js/build/openledger.js',
            filters='jsmin', output='js/build/openledger.min.js')
assets.register('js_all', js)

@application.before_first_request
def connect_to_search():
    from openledger import search
    es = search.init_es()
    connections.add_connection('default', es)

# Put these after the app code to avoid circular imports
from openledger import views
