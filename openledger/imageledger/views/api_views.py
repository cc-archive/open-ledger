import logging

from django.http import Http404, JsonResponse, HttpResponse, QueryDict
from django.views import View

from imageledger import models, api

log = logging.getLogger(__name__)

API_BASE = '/api/v1/'

class ListAPI(View):

    def get(self, request, slug):
        lst = api.get_list(slug)
        if not lst:
            raise Http404
        images = [serialize_image(img) for img in lst.images.all().order_by("-created_on")]
        return JsonResponse({'title': lst.title,
                             'description': lst.description,
                             'slug': lst.slug,
                             'creator_displayname': lst.creator_displayname,
                             'images': images,})

class ListsAPI(View):

    # Might want to specifically label this as for autocomplete since it's limited by design
    def get(self, request, match_method='startswith', limit=5):
        """Search for lists, optionally by title"""
        lsts = api.get_lists(title=request.GET.get('title'),
                             match_method=match_method)
        output = []
        for lst in lsts[0:limit]:
            output.append(serialize_list(lst))
        return JsonResponse({'lists': output})

    def post(self, request):
        if not request.POST.get('title'):
            r = JsonResponse({'message': "'Title' is a required field"})
            r.status_code=422
            return r
        lst = api.create_list(request.POST.get('title'), request.POST.getlist('identifier'))
        r = JsonResponse(serialize_list(lst))
        r.status_code = 201
        return r

    def delete(self, request):
        # FIXME will need to deal with auth here, we shouldn't allow deletion of
        # owned lists, and maybe should just harvest anon lists that have no activity?
        r = QueryDict(request.body)
        if not r.get('slug'):
            r = JsonResponse({'message': "'Slug' is a required field"})
            r.status_code = 422
            return r
        lst = api.delete_list(r.get('slug'))
        if not lst:
            raise Http404
        r = JsonResponse({})
        r.status_code=204
        return r

    def put(self, request):
        # FIXME same issue as above, don't allow randos to modify other people's lists
        # If 'title' and not 'slug' is supplied, this will be a CREATE as well
        r = QueryDict(request.body)

        status_code = 422
        if r.get('slug'):
            lst = api.update_list(r.get('slug'), image_identifiers=r.getlist('identifier'))
            status_code = 200
        else:
            if r.get('title'):
                lst = api.create_list(r.get('title'), r.getlist('identifier'))
                status_code = 201
            else:
                r = JsonResponse({'message': "One of 'slug' or 'title' is required"})
                r.status_code=422
                return r
        if not lst:
            r = HttpResponse()
            r.status_code = 422
            return r
        r = JsonResponse(serialize_list(lst))
        r.status_code=status_code
        return r

class ListImagesAPI(View):
    """Methods that operate against images within lists"""
    def post(self, request):
        if not request.POST.get('slug'):
            r = JsonResponse({'message':"'Slug' is a required field"})
            r.status_code=422
            return r

        resp = api.add_image_to_list(request.POST.get('slug'), image_identifier=request.POST.get('identifier'))
        if not resp:
            raise Http404
        image, lst = resp
        if not image:
            raise Http404
        r = JsonResponse(serialize_list(lst))
        r.status_code=201
        return r

    def delete(self, request):
        r = QueryDict(request.body, encoding=request._encoding)
        if not r.get('slug'):
            r = JsonResponse({'message': "'Slug' is a required field"})
            r.status_code=422
            return r
        resp = api.delete_image_from_list(r.get('slug'), image_identifier=r.get('identifier'))
        if not resp:
            raise Http404
        image, lst = resp
        if not image:
            raise Http404
        r= JsonResponse(serialize_list(lst))
        r.status_code=204
        return r


def serialize_image(img):
    """Return a serialization of an Image db object suitable for use in the API"""
    return {'identifier': img.identifier,
            'title': img.title,
            'url': img.url,
            'creator': img.creator}

def serialize_list(lst):
    """Return a serialization of a List db object suitable for use in the API"""
    return {'title': lst.title,
            'slug': lst.slug,
            'created_on': lst.created_on,
            'updated_on': lst.updated_on,
            'creator_displayname': lst.creator_displayname,
            'images': [serialize_image(img) for img in lst.images.all()]}
