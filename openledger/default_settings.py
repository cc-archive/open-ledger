import os

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
