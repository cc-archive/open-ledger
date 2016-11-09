import argparse
from datetime import datetime
import logging
import requests

from openledger import app, models
from elasticsearch import Elasticsearch, helpers, RequestsHttpConnection
from aws_requests_auth.aws_auth import AWSRequestsAuth
from elasticsearch_dsl.connections import connections
from elasticsearch_dsl import DocType, String, Date, Nested, Boolean, \
    analyzer, InnerObjectWrapper, Completion, Search

from sqlalchemy import orm

CHUNK_SIZE = 1000

console = logging.StreamHandler()
log = logging.getLogger(__name__)
log.addHandler(console)
log.setLevel(logging.INFO)

class Results(object):
    """A simple object prototype for collections of results"""

    def __init__(self, page=0, pages=0):
        self.page = page
        self.pages = pages
        self.items = []

class Image(DocType):
    title = String()
    identifier = String()
    creator = String()
    creator_url = String()
    tags = String(multi=True)
    created_on = Date()
    url = String()
    thumbnail = String()
    provider = String()
    source = String()
    license = String()
    license_version = String()
    foreign_landing_url = String()

    class Meta:
        index = "openledger"

def db_image_to_index(db_image):
    """Map an Image record to a record in the ESL DSL."""
    image = Image(title=db_image.title,
                  creator=db_image.creator,
                  created_on=db_image.created_on,
                  creator_url=db_image.creator_url,
                  identifier=db_image.identifier,
                  url=db_image.url,
                  thumbnail=db_image.thumbnail,
                  provider=db_image.provider,
                  source=db_image.source,
                  license=db_image.license,
                  foreign_landing_url=db_image.foreign_landing_url,
                  _id=db_image.identifier,
                  tags=db_image.tags_list)
    if db_image.tags_list:
        log.debug("Tags for %s: %s", image.title, ", ".join(image.tags))
    return image

def index_all_images():
    """Index every record in the database as efficiently as possible"""
    es = init()
    batches = []
    Image.init()
    mapping = Image._doc_type.mapping
    mapping.save('openledger')

    for db_image in models.Image.query.yield_per(CHUNK_SIZE):
        #log.debug("Indexing database record %s", db_image.identifier)
        image = db_image_to_index(db_image)
        if len(batches) > CHUNK_SIZE:
            log.debug("Pushing batch of %d records to ES", len(batches))
            helpers.bulk(es, batches)
            batches = []  # Clear the batch size
        else:
            batches.append(image.to_dict(include_meta=True))

    helpers.bulk(es, batches)

def init_es():
    if app.config['DEBUG']:
        return Elasticsearch(host=app.config['ELASTICSEARCH_URL'],
                             port=app.config['ELASTICSEARCH_PORT'],)

    auth = AWSRequestsAuth(aws_access_key=app.config['AWS_ACCESS_KEY_ID'],
                           aws_secret_access_key=app.config['AWS_SECRET_ACCESS_KEY'],
                           aws_host=app.config['ELASTICSEARCH_URL'],
                           aws_region='us-west-1',
                           aws_service='es')
    auth.encode = lambda x: bytes(x.encode('utf-8'))
    es = Elasticsearch(host=app.config['ELASTICSEARCH_URL'],
                       port=app.config['ELASTICSEARCH_PORT'],
                       connection_class=RequestsHttpConnection,
                       http_auth=auth)
    return es

def init():
    """Initialize all search objects"""
    es = init_es()
    connections.add_connection('default', es)
    log.debug("Initializing search objects for connection %s", app.config['ELASTICSEARCH_URL'])
    return es

if __name__ == '__main__':
    # Run me as python -m openledger.search
    parser = argparse.ArgumentParser()
    parser.add_argument("--verbose",
                        action="store_true",
                        default=False,
                        help="Be very chatty and run logging at DEBUG")
    args = parser.parse_args()
    if args.verbose:
        log.setLevel(logging.DEBUG)
    index_all_images()
