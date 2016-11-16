SECRET_KEY = 'XXX'
DEBUG=False

# API-specific
API_500PX_KEY = 'XXX'
API_500PX_SECRET = 'XXX'
API_RIJKS = 'XXX'
FLICKR_KEY = 'XXX'
FLICKR_SECRET = 'XXX'

# Database-specific
SQLALCHEMY_DATABASE_URI = 'postgresql://{}:{}@{}:{}/{}'.format('cctest',
                                                               'cctest',
                                                               'localhost',
                                                               '5432',
                                                               'openledgertest')

SQLALCHEMY_TRACK_MODIFICATIONS = False

DEBUG_TB_ENABLED = False

TESTING=True
