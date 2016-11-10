import logging
from urllib.parse import urlencode

from elasticsearch_dsl import Search, Q
from flask import Flask, jsonify, request, abort, session, make_response, redirect, url_for
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

from openledger import app, forms, models

log = logging.getLogger(__name__)
console = logging.StreamHandler()
log.addHandler(console)
log.setLevel(logging.INFO)

# The primary identifier we use to assert whether a user is logged in (via CAS)
AUTH_SESSION_IDENTIFIER = 'CAS_USERNAME'

@app.route('/auth/redirect')
def auth_redirect():
    """Receive requests from the CAS login endpoint"""
    attrs = session.get('CAS_ATTRIBUTES')
    ccid = attrs.get('cas:global')
    nickname = attrs.get('cas:nickname')
    email = session.get(AUTH_SESSION_IDENTIFIER)
    if not attrs:
        raise Exception("attrs not found in session %s, %s", session, session.get('CAS_ATTRIBUTES'))
    if not email:
        raise Exception("email not found in %s", session)
    if not ccid:
        raise Exception("ccid not found in attrs %s", attrs)

    try:
        user = models.User.query.filter(models.User.ccid==ccid).one()
    except NoResultFound:
        log.debug("Creating new user with ccid %s, nickname %s", ccid, nickname)
        user = models.User(ccid=ccid, nickname=nickname, email=email)
        models.db.session.add(user)
        models.db.session.commit()

    resp = make_response(redirect(url_for('fulltext')))
    resp.set_cookie('ol-identifier', user.identifier)  # session cookie only, reauth will be required
    return resp

@app.route('/auth/logout')
def auth_logout():
    """Locally log a user out before logging them out from CAS as well"""
    redirect_url = urlencode({"service": request.url + '/' + url_for('fulltext')})

    logout_url = "{}{}?{}".format(app.config['CAS_SERVER'],
                                  app.config['CAS_LOGOUT_ROUTE'],
                                  redirect_url)
    resp = make_response(redirect(logout_url))
    resp.delete_cookie('ol-identifier')
    resp.delete_cookie('session')
    return resp

@app.route('/api/v1/auth/logged-in') 
def logged_in():
    """Standalone view to determine whether the current user is logged in, for use in
    JS requests. Returns a JSON response, `logged_in`, true or false.

    This is just a helper function: no actual authentication should be assumed just because
    this easily-spoofed function returns true!
    """
    return make_response(jsonify({'logged-in': AUTH_SESSION_IDENTIFIER in session}))
