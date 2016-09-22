import requests
from urllib.parse import parse_qs
from requests_oauthlib import OAuth1Session, OAuth1
from oauthlib.oauth2 import BackendApplicationClient

from openledger import app

BASE_URL = 'https://api.500px.com'
ENDPOINT_PHOTOS = BASE_URL + '/v1/photos/search'

IMAGE_SIZE_THUMBNAIL = 3  # 200x200

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
    "ALL-CC": "1,2,3,4,5,6,7,8"
}
LICENSE_LOOKUP = {v: k for k, v in LICENSES.items()}

def auth():
    return OAuth1(app.config['API_500PX_KEY'], client_secret=app.config['API_500PX_SECRET'])

def photos(search=None, licenses=LICENSES["ALL-CC"]):
    params = {
        'license_type': licenses,
        'term': search,
        'image_size': IMAGE_SIZE_THUMBNAIL,
    }
    r = requests.get(ENDPOINT_PHOTOS, params=params, auth=auth())
    return r.json()

if __name__ == '__main__':
    photos(search='dog')
