import logging
from functools import reduce

from django.conf import settings
from django.shortcuts import render, get_object_or_404
from django.views.decorators.csrf import ensure_csrf_cookie
from elasticsearch_dsl import Search, Q
from elasticsearch_dsl.connections import connections

from imageledger import forms, search, licenses, models

log = logging.getLogger(__name__)

@ensure_csrf_cookie
def index(request):
    res = search.do_search(request);
    return render(request, 'results.html',
                  {'form': res['form'],
                   'work_types': settings.WORK_TYPES,
                   'results': res['results'],})

def by_image(request):
    """Load an image in detail view, passing parameters by query string so that
    we can either load an image from an external provider or from our own datastore."""
    license_version = licenses.license_map_from_partners()[request.GET.get('provider')]['version']
    license_url = licenses.get_license_url(request.GET.get('license'), license_version)
    remaining = dict((k, request.GET[k]) for k in request.GET)  # The vals in request.GET are lists, so flatten
    remaining.update({'license_version': license_version})
    return render(request, 'detail.html',
                  {'image': remaining,
                   'license_url': license_url,
                   })


def detail(request, identifier):
    obj = get_object_or_404(models.Image, identifier=identifier)
    if request.user.is_authenticated():
        # Is it a favorite?
        obj.is_favorite = models.Favorite.objects.filter(user=request.user, image=obj).exists()
    license_url = licenses.get_license_url(obj.license, obj.license_version)
    return render(request, 'detail.html',
                  {'image': obj,
                   'license_url': license_url,})
