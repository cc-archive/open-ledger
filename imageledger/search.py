import argparse
from datetime import datetime
import logging
import requests
import time

from django.conf import settings

from elasticsearch import Elasticsearch, helpers, RequestsHttpConnection
from elasticsearch.exceptions import ConnectionError
from aws_requests_auth.aws_auth import AWSRequestsAuth
from elasticsearch_dsl.connections import connections
from elasticsearch_dsl import DocType, String, Date, Nested, Boolean, \
    analyzer, InnerObjectWrapper, Completion, Search

CHUNK_SIZE = 1000

MAX_CONNECTION_RETRIES = 10
RETRY_WAIT = 5  # Number of sections to wait before retrying

log = logging.getLogger()

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
    removed_from_source = Boolean()

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
                  removed_from_source=db_image.removed_from_source,
                  _id=db_image.identifier,
                  tags=db_image.tags_list)
    return image

def init_es():
    log.info("connecting to %s %s", settings.ELASTICSEARCH_URL, settings.ELASTICSEARCH_PORT)
    auth = AWSRequestsAuth(aws_access_key=settings.AWS_ACCESS_KEY_ID,
                           aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                           aws_host=settings.ELASTICSEARCH_URL,
                           aws_region='us-west-1',
                           aws_service='es')
    auth.encode = lambda x: bytes(x.encode('utf-8'))
    es = Elasticsearch(host=settings.ELASTICSEARCH_URL,
                       port=settings.ELASTICSEARCH_PORT,
                       connection_class=RequestsHttpConnection,
                       http_auth=auth)
    return es

def init():
    """Initialize all search objects"""
    es = init_es()
    connections.add_connection('default', es)
    log.debug("Initializing search objects for connection %s:%s", settings.ELASTICSEARCH_URL, settings.ELASTICSEARCH_PORT)
    return es
