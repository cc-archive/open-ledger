from flask import Flask
from flask_debugtoolbar import DebugToolbarExtension

application = Flask(__name__)
app = application  # Workaround for AWS-specific configuration
app.config.from_pyfile('default_settings.py')
#toolbar = DebugToolbarExtension(app)

# Put these after the app code to avoid circular imports
from openledger import views
