import requests
from urllib.parse import parse_qs
from secret import API_500PX_KEY, API_500PX_SECRET
from requests_oauthlib import OAuth1Session, OAuth1
from oauthlib.oauth2 import BackendApplicationClient

BASE_URL = 'https://api.500px.com'
ENDPOINT_PHOTOS = BASE_URL + '/v1/photos/search'

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

def auth():
    return OAuth1(API_500PX_KEY, client_secret=API_500PX_SECRET)

def photos(search=None, licenses=LICENSES["ALL-CC"]):
    params = {
        'license_type': licenses,
        'term': search
    }
    r = requests.get(ENDPOINT_PHOTOS, params=params, auth=auth())
    return r.json()

if __name__ == '__main__':
    photos(search='dog')
