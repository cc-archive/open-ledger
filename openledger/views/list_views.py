import logging

from elasticsearch_dsl import Search
from flask import Flask, render_template, request, abort, jsonify, make_response
from flask.views import MethodView
from sqlalchemy import and_, or_, not_, distinct

from openledger import app, models, api

log = logging.getLogger(__name__)

class ListViews(MethodView):

    def get(self, slug):
        """Web interface to get a list by slug"""
        lst = api.get_list(slug)
        if not lst:
            abort(404)
        images = lst.images.order_by(models.Image.created_on.desc()).all()
        return render_template('list.html',
                               lst=lst,
                               images=images)

    def post(self, slug):
        """Edit a list's metadata"""
        # This is for editing properties of the list itself only; adding/removing
        # images is best done using the JS API because of the inherent clunkiness
        # TODO this should be restricted to the owner of the list when that's possible
        lst = api.get_list(slug)
        if not lst:
            abort(404)



app.add_url_rule('/list/<slug>', view_func=ListViews.as_view('list-view'))
