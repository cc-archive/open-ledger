from flask import Flask
from flask_debugtoolbar import DebugToolbarExtension

app = Flask(__name__, instance_relative_config=True)
app.config.from_pyfile('config.py')
toolbar = DebugToolbarExtension(app)

# Put these after the app code to avoid circular imports
from openledger import views
