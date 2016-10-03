from flask import Flask

app = Flask(__name__, instance_relative_config=True)
app.config.from_pyfile('config.py')

# Put these after the app code to avoid circular imports
from openledger import views
