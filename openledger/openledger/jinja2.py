from urllib.parse import urlencode


from django.contrib.staticfiles.storage import staticfiles_storage
from django.urls import reverse

from jinja2 import Environment

def environment(**options):
    env = Environment(**options)
    env.globals.update({
        'static': staticfiles_storage.url,
        'url': url_tag,
        'url_for': url_tag,
    })
    return env

def url_tag(view, **kwargs):
    url = reverse(view)
    if kwargs:
        url += '?' + urlencode(kwargs)
    return url

def pluralize(number, singular='', plural='s'):
    try:
        number = int(number)
    except ValueError:
        number = 0
    finally:
        return singular if number == 1 else plural
