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
    SQLALCHEMY_DATABASE_URI = 'postgresql://{}:{}@{}:{}/{}'.format(os.environ['RDS_USERNAME'],
                                                                   os.environ['RDS_PASSWORD'],
                                                                   os.environ['RDS_HOSTNAME'],
                                                                   os.environ['RDS_PORT'],
                                                                   os.environ['RDS_DB_NAME'])

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    ELASTICSEARCH_URL = os.environ['ELASTICSEARCH_URL']
