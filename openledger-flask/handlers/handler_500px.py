import requests
from urllib.parse import parse_qs
from requests_oauthlib import OAuth1Session, OAuth1
from oauthlib.oauth2 import BackendApplicationClient

from openledger import app
from openledger.licenses import license_match

BASE_URL = 'https://api.500px.com'
ENDPOINT_PHOTOS = BASE_URL + '/v1/photos/search'

IMAGE_SIZE_THUMBNAIL = 3  # 200x200
IMAGE_SIZE_FULL = 1080 # 1080x

# 500px will return these values as integers, so keep them as integers
LICENSES = {
    "BY": 4,
    "BY-NC": 1,
    "BY-ND": 5,
    "BY-SA": 6,
    "BY-NC-ND": 2,
    "BY-NC-SA": 3,
    "PDM": 7,
    "CC0": 8,
}
LICENSE_VERSION = "3.0"

LICENSE_LOOKUP = {v: k for k, v in LICENSES.items()}

def auth():
    return OAuth1(app.config['API_500PX_KEY'], client_secret=app.config['API_500PX_SECRET'])

def photos(search=None, licenses=["ALL"], page=1, per_page=20, **kwargs):
    params = {
        'license_type': license_match(licenses, LICENSES),
        'term': search,
        'page': page,
        'rpp': per_page,
        'image_size': "%s,%s" % (IMAGE_SIZE_THUMBNAIL, IMAGE_SIZE_FULL)
    }
    r = requests.get(ENDPOINT_PHOTOS, params=params, auth=auth())
    return r.json()

if __name__ == '__main__':
    photos(search='dog')
