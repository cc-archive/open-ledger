from flask import Flask
from elasticsearch_dsl.connections import connections

application = Flask(__name__)
app = application  # Workaround for AWS-specific configuration
app.config.from_pyfile('default_settings.py')

@application.before_first_request
def connect_to_search():
    from openledger import search
    es = search.init_es()
    connections.add_connection('default', es)

# Put these after the app code to avoid circular imports
from openledger import views
