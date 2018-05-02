from openledger.settings import *

STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
SECRET_KEY = 'SECRET_KEY_FOR_TESTING'

API_500PX_KEY = 'TESTING'
API_500PX_SECRET = 'TESTING'

API_RIJKS = 'TESTING'
NYPL_KEY = 'TESTING'
FLICKR_KEY = 'TESTING'
FLICKR_SECRET = 'TESTING'

ELASTICSEARCH_URL = 'es'
ELASTICSEARCH_PORT = 9200
ELASTICSEARCH_INDEX = 'testing'

AWS_ACCESS_KEY_ID = "TESTING"
AWS_SECRET_ACCESS_KEY = "TESTING"

ALLOWED_HOSTS = ['localhost']
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'openledger',
        'USER': 'postgres',
        'HOST': 'db',
        'PASSWORD': 'deploy',
        'PORT': 5432,
    }
}
LOGGING = {
     'version': 1,
     'disable_existing_loggers': False,
     'filters': {
         'require_debug_false': {
             '()': 'django.utils.log.RequireDebugFalse'
         }
     },
     'handlers': {
         'mail_admins': {
             'level': 'ERROR',
             'filters': ['require_debug_false'],
             'class': 'django.utils.log.AdminEmailHandler'
         },
         'console': {
             'level': 'DEBUG',
             'class': 'logging.StreamHandler'
         },
     },
     'loggers': {
         'django.request': {
             'handlers': ['mail_admins'],
             'level': 'ERROR',
             'propagate': True,
         },
         'imageledger': {
             'handlers': ['console'],
             'level': 'DEBUG'
         },

     }
}

TESTING=True
