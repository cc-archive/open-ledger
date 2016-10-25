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

app.add_url_rule('/list/<slug>', view_func=ListViews.as_view('list-view'))
