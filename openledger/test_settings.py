from openledger.settings import *

STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
SECRET_KEY = 'SECRET_KEY_FOR_TESTING'
ALLOWED_HOSTS = ['localhost']
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
