import itertools
import logging
import time
from pprint import pprint

import requests

from django.conf import settings
from imageledger import models, signals, search
from django.db.utils import IntegrityError
from django.utils import timezone

from imageledger.handlers.utils import *

BASE_URL = 'http://www.metmuseum.org'
ENDPOINT_PHOTOS = BASE_URL + '/api/collection/openaccessobjectids'
ENDPOINT_DETAIL = BASE_URL + '/api/collection/collectionobject/'
ENDPOINT_BASE_IMAGE_URL = 'http://images.metmuseum.org/crdimages/'
FOREIGN_LANDING_BASE_URL = 'http://www.metmuseum.org/art/collection/search/'

LICENSE_VERSION = "1.0"
LICENSE_URL = "https://creativecommons.org/publicdomain/zero/1.0/"

PROVIDER_NAME = "met"
SOURCE_NAME = "met"

# Labels found in the data that we'll assign to the 'creator' field
CREATOR_LABELS_RAW = ['Role', 'Architect', 'Armorer', 'Artist', 'Artist and architect',
                  'Artist and engraver', 'Artist and publisher', 'Author', 'Barrelsmith', 'Binder',
                  'Blacksmith', 'Bladesmith', 'Calligrapher', 'Collector', 'Colophon writer', 'Correspondent',
                  'Couture Line', 'Culture', 'Damascener', 'Decorator', 'Dedicatee', 'Department Store',
                  'Design House', 'Designer', 'Draftsman', 'Editor', 'Enameler', 'Engraver',
                  'Entrepreneur', 'Etcher', 'Factory', 'Factory director', 'Factory owner', 'Fittings maker',
                  'Former Attribution', 'Founder', 'Goldsmith', 'Grip wrapper', 'Gun assembler',
                  'Gunsmith', 'Hilt Maker', 'Illuminator', 'Illustrator', 'Inlayer', 'Inscriber',
                  'Inventor', 'Iron-chiseler', 'Lacquer worker', 'Lithographer', 'Lock maker', 'Maker',
                  'Manufactory', 'Manufacturer', 'Modeler', 'Mount maker', 'Patentee', 'Patron',
                  'Person in Photograph', 'Photo Source', 'Photographer', 'Photographer and Photo Source',
                  'Photographer, Epigrapher', 'Photography Studio', 'Poet', 'Printer', 'Printmaker',
                  'Publisher', 'Purveyor', 'Restorer/Conservator', 'Retailer', 'Scribe', 'Scriptorium',
                  'Secondary Line', 'Silversmith', 'Sitter', 'Source', 'Steel-chiseler', 'Stock maker',
                  'Stock polisher', 'Subject', 'Subject of book', 'Sword cutler', 'Sword maker', 'Swordsmith',
                  'Translator', 'Typographer', 'Workshop director']
# Add the colon variant; Met data quirk
CREATOR_LABELS_RAW += [c + ':' for c in CREATOR_LABELS_RAW]
CREATOR_LABELS = set(CREATOR_LABELS_RAW)

DELAY_SECONDS = 0.5  # Time to wait between API requests

THUMBNAIL_WIDTH = 200

log = logging.getLogger(__name__)

def photos(search=None, page=1, per_page=20, **kwargs):
    # This will retrieve the complete collection of openly-licensed images
    # Rijks pages are zero-indexed, so always subtract one before the request
    params = {}
    r = requests.get(ENDPOINT_PHOTOS, params=params)
    results = r.json()
    return results

def serialize(result):
    """For a given Met result, map that to our database"""
    imageinfos = result['ImageInfo']
    thumbnail = None
    url = None
    for info in imageinfos:
        if info['PrimaryDisplay']:
            # Use this one
            thumbnail = ENDPOINT_BASE_IMAGE_URL + info['Thumbnail']
            url = ENDPOINT_BASE_IMAGE_URL + info['LargeWebsite']
            break
    if not url:
        log.warning("Did not get an image URL for %s", result)
        return
    image = models.Image(url=url)
    image.provider = PROVIDER_NAME
    image.source = SOURCE_NAME

    # Creator might be a few fields
    tombstone = result['Tombstone']
    for t in tombstone:
        if t['Name'] in CREATOR_LABELS:
            image.creator = t['Value']
        # TBD other metadata
    image.thumbnail = thumbnail
    image.license = "cc0"
    image.license_version = '1.0'
    image.foreign_identifier = result['CollectionObject']['CRDID']
    image.foreign_landing_url = FOREIGN_LANDING_BASE_URL + str(image.foreign_identifier)
    image.title = result['CollectionObject']['Title']
    image.identifier = signals.create_identifier(image.url)
    image.last_synced_with_source = timezone.now()
    log.info("Adding image %s (%s) identifier %s", image.title, image.foreign_identifier, image.identifier)
    return image

def walk(page=1, per_page=200):
    """Walk through a set of search results and collect items to serialize"""
    results = photos()
    for identifier in results:
        # Retrieve the result
        url = ENDPOINT_DETAIL + str(identifier)
        r = requests.get(url, headers={'accept': 'text/html'}) # Met API quirk, ought to be application/json
        result = r.json()
        yield result
        time.sleep(DELAY_SECONDS)