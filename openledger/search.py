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

class Image(DocType):
    title = String()
    identifier = String()
    tags = String(multi=True)
    created_at = Date()
    class Meta:
        index = "openledger"

def db_image_to_index(db_image):
    """Map an Image record to a record in the search index"""
    image = Image(title=db_image.title,
                  identifier=db_image.identifier,
                  tags=[t.name for t in db_image.tags])
    image.save()
    log.info("Created image with id %s", image)

def index_image():
    image = Image(title='test', identifier='xxx')
    image.save()

def simple_search():
    s = Search()
    s.query()
    response = s.execute()
    log.info(response)

def init():
    """Initialize all search objects"""
    connections.create_connection(hosts=[{'host': app.config['ELASTICSEARCH_URL'], 'port': 80}])
    log.info("Initializing search objects for connection %s", app.config['ELASTICSEARCH_URL'])
    Image.init()

if __name__ == '__main__':
    init()
    simple_search()

#    db_image = models.Image.query.filter(models.Image.creator=='Liza').first()
#    db_image_to_index(db_image)
