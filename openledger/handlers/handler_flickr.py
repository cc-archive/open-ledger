# encoding: utf-8

import logging

requests_log = logging.getLogger("flickrapi")
requests_log.propagate = False

import flickrapi

from openledger import app

LICENSES = {
    "BY": 4,
    "BY-NC": 2,
    "BY-ND": 6,
    "BY-SA": 5,
    "BY-NC-ND": 3,
    "BY-NC-SA": 1,
    "PDM": 7,
    "CC0": 9,
    "ALL-CC": "1,2,3,4,5,6",
}

LICENSE_LOOKUP = {v: k for k, v in LICENSES.items()}

def auth():
    return flickrapi.FlickrAPI(app.config['FLICKR_KEY'],
                               app.config['FLICKR_SECRET'],
                               format='parsed-json')

def photos(search=None, licenses=LICENSES["ALL-CC"]):
    flickr = auth()
    photos = flickr.photos.search(safe_search=1,  # safe-search on
                         content_type=1,  # Photos only, no screenshots
                         license=licenses,
                         text=search,
                         extras='url_m,owner_name,license',
                         sort='relevance',
                         per_page=20)  # FIXME make this configurable and global to all handlers
    return photos
