import requests

from openledger import app

BASE_URL = 'https://www.rijksmuseum.nl'
ENDPOINT_PHOTOS = BASE_URL + '/api/en/collection'

LIMIT = 20

def photos(search=None):
    params = {
        'format': 'JSON',
        'q': search,
        'key': app.config['API_RIJKS'],
        'imgonly': 'True',  # This doesn't seem to have an effect, so filter
        'culture': 'en',
        'ps': 30,  # Results per page
    }
    r = requests.get(ENDPOINT_PHOTOS, params=params)
    results = r.json()

    # Since the imgonly parameter doesn't work, filter ourselves and cut down the
    # result set
    filtered = [res for res in results.get('artObjects') if res.get('webImage')]
    results['artObjects'] = filtered[:LIMIT]
    return results
