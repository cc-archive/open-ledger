import requests

from app import app

BASE_URL = 'https://www.rijksmuseum.nl'
ENDPOINT_PHOTOS = BASE_URL + '/api/en/collection'

def photos(search=None):
    params = {
        'format': 'JSON',
        'q': search,
        'key': app.config['API_RIJKS'],
        'imgonly': True,
        'culture': 'en',
    }
    r = requests.get(ENDPOINT_PHOTOS, params=params)
    return r.json()
