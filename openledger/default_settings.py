import os

# Auth
CAS_SERVER = "https://login.creativecommons.org"
CAS_AFTER_LOGIN = "fulltext"
CAS_LOGIN_ROUTE = "/login"

try:
    from instance.config import *

except ImportError:
    # Import from env
    SECRET_KEY = os.environ.get('SECRET_KEY')
    DEBUG=os.environ.get('DEBUG')

    # API-specific
    API_500PX_KEY = os.environ.get('API_500PX_KEY')
    API_500PX_SECRET = os.environ.get('API_500PX_SECRET')
    API_RIJKS = os.environ.get('API_RIJKS')
    FLICKR_KEY = os.environ.get('FLICKR_KEY')
    FLICKR_SECRET = os.environ.get('FLICKR_SECRET')

    # Database-specific
    SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI')

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    ELASTICSEARCH_URL = os.environ.get('ELASTICSEARCH_URL')

    AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')

    # Static assets
    ASSETS_AUTO_BUILD=False
