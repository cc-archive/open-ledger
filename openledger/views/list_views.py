import logging

from elasticsearch_dsl import Search
from flask import Flask, render_template, request, abort, url_for, make_response, redirect
from flask.views import MethodView
from sqlalchemy import and_, or_, not_, distinct
from werkzeug.datastructures import MultiDict

from openledger import app, models, api, forms

log = logging.getLogger(__name__)
console = logging.StreamHandler()
log.addHandler(console)
log.setLevel(logging.INFO)

class ListViews(MethodView):

    def get(self, slug):
        """Web interface to get a list by slug"""
        lst = api.get_list(slug)
        if not lst:
            abort(404)
        images = lst.images.order_by(models.Image.created_on.desc()).all()

        form = forms.ListForm(obj=lst)
        return render_template('list.html',
                               lst=lst,
                               form=form,
                               images=images)

    def post(self, slug):
        """Edit a list's metadata"""
        # This is for editing properties of the list itself only; adding/removing
        # images is best done using the JS API because of the inherent clunkiness

        # TODO this should be restricted to the owner of the list when that's possible
        form = forms.ListForm()

        if form.validate_on_submit():
            lst = api.get_list(slug)
            if not lst:
                abort(404)
            lst.description = form.description.data
            lst.title = form.title.data
            lst.is_public = form.is_public.data
            models.db.session.add(lst)
            models.db.session.commit()
            return redirect(url_for('list-view', slug=slug))
        else:
            log.warn("Form did not validate")
            return self.get(slug)

app.add_url_rule('/list/<slug>', view_func=ListViews.as_view('list-view'))
