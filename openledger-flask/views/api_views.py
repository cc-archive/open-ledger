import logging

from flask import Flask, render_template, request, abort, jsonify, make_response
from flask.views import MethodView
from sqlalchemy.exc import IntegrityError

from openledger import app
from openledger import models, forms

log = logging.getLogger(__name__)

API_BASE = '/api/v1/'

class ListAPI(MethodView):

    def get(self, request, slug):
        lst = api.get_list(slug)
        if not lst:
            abort(404)
        images = [serialize_image(img) for img in lst.images.order_by(models.Image.created_on.desc()).all()]
        return jsonify(title=lst.title,
                       description=lst.description,
                       slug=lst.slug,
                       creator_displayname=lst.creator_displayname,
                       images=images,)

app.add_url_rule(API_BASE + 'list/<slug>', view_func=ListAPI.as_view('list'))

class ListsAPI(MethodView):

    # Might want to specifically label this as for autocomplete since it's limited by design
    def get(self, request, match_method='startswith', limit=5):
        """Search for lists, optionally by title"""
        lsts = api.get_lists(title=request.GET.get('title'),
                             match_method=match_method)
        output = []
        for lst in lsts[0:limit]:
            output.append(serialize_list(lst))
        return make_response(jsonify(lists=output))

    def post(self, request):
        if not request.POST.get('title'):
            return make_response(jsonify(message="'Title' is a required field"), 422)
        lst = api.create_list(request.POST.get('title'), request.POST.getlist('identifier'))
        return make_response(jsonify(serialize_list(lst)), 201)

    def delete(self, request):
        # FIXME will need to deal with auth here, we shouldn't allow deletion of
        # owned lists, and maybe should just harvest anon lists that have no activity?
        if not request.META.get('slug'):
            return make_response(jsonify(message="'Slug' is a required field"), 422)
        lst = api.delete_list(request.META.get('slug'))
        if not lst:
            abort(404)
        return make_response(jsonify(), 204)

    def put(self, request):
        # FIXME same issue as above, don't allow randos to modify other people's lists
        # If 'title' and not 'slug' is supplied, this will be a CREATE as well
        status_code = 422
        if request.META.get('slug'):
            lst = api.update_list(request.META.get('slug'), image_identifiers=request.META.get('identifier'))
            status_code = 200
        else:
            if request.form.get('title'):
                lst = api.create_list(request.META.get('title'), request.META.get('identifier'))
                status_code = 201
            else:
                return make_response(jsonify(message="One of 'slug' or 'title' is required"), 422)
        if not lst:
            abort(status_code)
        return make_response(jsonify(serialize_list(lst)), status_code)

app.add_url_rule(API_BASE + 'lists', view_func=ListsAPI.as_view('lists'))

class ListImageAPI(MethodView):
    """Methods that operate against images within lists"""
    def post(self, request):
        if not request.form.get('slug'):
            return make_response(jsonify(message="'Slug' is a required field"), 422)
        try:
            resp = api.add_image_to_list(request.form.get('slug'), image_identifier=request.form.get('identifier'))
        except IntegrityError as e:
            # Check whether this was due to a duplicate, and if so, return a 304 Not Modified
            models.db.session.rollback()
            lst = api.get_list(request.form.get('slug'))
            if request.form.get('identifier') in [img.identifier for img in lst.images]:
                return make_response(jsonify(serialize_list(lst)), 200)
            # Otherwise, keep raising the exception, as something else was wrong
            raise e
        if not resp:
            abort(404)
        image, lst = resp
        if not image:
            abort(404)
        return make_response(jsonify(serialize_list(lst)), 201)

    def delete(self, request):
        if not request.form.get('slug'):
            return make_response(jsonify(message="'Slug' is a required field"), 422)
        resp = api.delete_image_from_list(request.form.get('slug'), image_identifier=request.form.get('identifier'))
        if not resp:
            abort(404)
        image, lst = resp
        if not image:
            abort(404)
        return make_response(jsonify(serialize_list(lst)), 204)


app.add_url_rule(API_BASE + 'list/images', view_func=ListImageAPI.as_view('list-images'))

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
            'images': [serialize_image(img) for img in lst.images]}
