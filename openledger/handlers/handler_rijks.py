import requests

from openledger import app

BASE_URL = 'https://www.rijksmuseum.nl'
ENDPOINT_PHOTOS = BASE_URL + '/api/en/collection'

def photos(search=None, page=1, per_page=20, **kwargs):
    # Rijks pages are zero-indexed, so always subtract one before the request
    p = int(page) - 1
    params = {
        'format': 'JSON',
        'q': search,
        'key': app.config['API_RIJKS'],
        'imgonly': 'True',  # This doesn't seem to have an effect, so filter
        'culture': 'en',
        'p': p, # Page number
        'ps': per_page,  # Results per page
    }
    r = requests.get(ENDPOINT_PHOTOS, params=params)
    results = r.json()

    # Since the imgonly parameter doesn't work, filter ourselves and cut down the result set
    filtered = [res for res in results.get('artObjects') if res.get('webImage')]
    results['artObjects'] = filtered[:per_page]

    # Rijks doesn't give us a nice set of pages, so do that ourselves
    results['page'] = int(page)
    results['pages'] = int(int(results['count']) / per_page)
    return results
