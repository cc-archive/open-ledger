from datetime import datetime
import logging

from openledger import app, models
from elasticsearch import Elasticsearch
from elasticsearch_dsl.connections import connections
from elasticsearch_dsl import DocType, String, Date, Nested, Boolean, \
    analyzer, InnerObjectWrapper, Completion, Search

console = logging.StreamHandler()
log = logging.getLogger(__name__)
log.addHandler(console)
log.setLevel(logging.DEBUG)

class Results(object):
    """A simple object prototype for collections of results"""

    def __init__(self, page=0, pages=0):
        self.page = page
        self.pages = pages
        self.items = []

class Result(object):
    """A simple object prototype for individual result items"""
    fields = ('title', 'url', 'creator', 'creator_url', 'foreign_landing_url',
              'license', 'identifier')
    def __init__(self, **kwargs):
        for f in self.fields:
            self.__setattr__(f, None)

        for k in kwargs:
            if k in self.fields:
                self.__setattr__(k, kwargs[k])


    @classmethod
    def from_elasticsearch(cls, sr):
        r = Result(title=sr.title,
                   url=sr.url,
                   creator=sr.creator,
                   creator_url=sr.creator_url,
                   foreign_landing_url=sr.foreign_landing_url,
                   identifier=sr.identifier,
                   license=sr.license)
        return r

class Image(DocType):
    title = String()
    identifier = String()
    creator = String()
    creator_url = String()
    tags = String(multi=True)
    created_at = Date()
    url = String()
    provider = String()
    source = String()
    license = String()
    foreign_landing_url = String()

    class Meta:
        index = "openledger"

def db_image_to_index(db_image):
    """Map an Image record to a record in the search index"""
    image = Image(title=db_image.title,
                  creator=db_image.creator,
                  creator_url=db_image.creator_url,
                  identifier=db_image.identifier,
                  url=db_image.url,
                  provider=db_image.provider,
                  source=db_image.source,
                  license=db_image.license,
                  foreign_landing_url=db_image.foreign_landing_url,
                  _id=db_image.identifier,
                  tags=[t.name for t in db_image.tags])
    created = image.save()
    log.info("Indexed image with id %s (created=%s)", image._id, created)


def init():
    """Initialize all search objects"""
    connections.create_connection(hosts=[{'host': app.config['ELASTICSEARCH_URL'], 'port': 80}])
    log.info("Initializing search objects for connection %s", app.config['ELASTICSEARCH_URL'])
    Image.init()

if __name__ == '__main__':
    init()

    for db_image in models.Image.query.filter(models.Image.creator=='Liza'):
        db_image_to_index(db_image)

    s = Search()
    s = s.query("match", title="greyhound")
    response = s.execute()
    for r in s:
        print("Image {} with title '{}'".format(r.identifier, r.title))
