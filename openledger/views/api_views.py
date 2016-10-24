import logging

from elasticsearch_dsl import Search
from flask import Flask, render_template, request, abort, jsonify, make_response
from flask.views import MethodView
from sqlalchemy import and_, or_, not_, distinct

from openledger import app, forms, licenses, search
from openledger import models

log = logging.getLogger(__name__)

API_BASE = '/api/v1/'

class ListAPI(MethodView):

    def get(self, slug):
        lst = models.List.query.filter(models.List.slug==slug).first()
        if not lst:
            abort(404)
        images = [serialize_image(img) for img in lst.images.order_by(models.Image.identifier).all()]
        return jsonify(title=lst.title,
                       description=lst.description,
                       slug=lst.slug,
                       creator_displayname=lst.creator_displayname,
                       images=images,
                       )

    def delete(self, slug):
        # FIXME will need to deal with auth here, we shouldn't allow deletion of
        # owned lists, and maybe should just harvest anon lists that have no activity?
        lst = models.List.query.filter(models.List.slug==slug).first()
        if not lst:
            abort(404)
        models.db.session.delete(lst)
        models.db.session.commit()
        return make_response('', 204)

    def put(self, slug):
        # FIXME same issue as above, don't allow randos to modify other people's lists
        lst = models.List.query.filter(models.List.slug==slug).first()
        if not lst:
            abort(404)
        images = models.Image.query.filter(models.Image.identifier.in_(request.form.getlist('image')))
        lst.images = images
        models.db.session.add(lst)
        models.db.session.commit()
        return make_response('', 200)

app.add_url_rule(API_BASE + 'list/<slug>', view_func=ListAPI.as_view('list'))

class ListsAPI(MethodView):

    def post(self):
        if not request.form.get('title'):
            return make_response(jsonify(message="'Title' is a required field"), 422)

        lst = models.List(title=request.form.get('title'))
        images = models.Image.query.filter(models.Image.identifier.in_(request.form.getlist('image')))
        lst.images = images
        models.db.session.add(lst)
        models.db.session.commit()
        return make_response(jsonify(slug=lst.slug), 201) # FIXME this should probably be a complete URL


app.add_url_rule(API_BASE + 'lists', view_func=ListsAPI.as_view('lists'))

def serialize_image(img):
    """Return a serialization of an image database suitable for use in the API"""
    return {'identifier': img.identifier,
            'title': img.title,
            'url': img.url,
            'creator': img.creator}
