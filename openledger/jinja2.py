import logging
from urllib.parse import urlencode, parse_qs


from django.contrib.staticfiles.storage import staticfiles_storage
from django.urls import reverse

from jinja2 import Environment

log = logging.getLogger(__name__)

def environment(**options):
    env = Environment(**options)
    env.globals.update({
        'static': staticfiles_storage.url,
        'url': url_tag,
        'url_for': url_tag,
        'url_with_form': url_with_form,
    })
    return env

def url_with_form(view, form, args, kwargs):
    """Expects a view name, a form, and optional arguments. The form's data will be
    serialized, with any overrides from kwargs applied. Args are passed through to `reverse`"""
    url = reverse(view, args=args)
    qs = form.data.urlencode()
    parsed = parse_qs(qs)
    if kwargs:
        parsed.update(kwargs)
    url = url + '?' + urlencode(parsed, doseq=True)

    return url

def url_tag(view, *args, **kwargs):
    url = reverse(view, args=args)
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
