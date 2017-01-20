import os
import newrelic.agent

newrelic.agent.initialize(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                       'newrelic.ini'))
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "openledger.settings")

application = get_wsgi_application()

from wsgi_basic_auth import BasicAuth
application = BasicAuth(application)
