"""
WSGI config for openledger project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.10/howto/deployment/wsgi/
"""

import os
import newrelic.agent
newrelic.agent.initialize(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                       'newrelic.ini'))
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "openledger.settings")

application = get_wsgi_application()
