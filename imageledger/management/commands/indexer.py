import logging

from elasticsearch import helpers
from django.core.management.base import BaseCommand, CommandError

from imageledger import models, search

console = logging.StreamHandler()
log = logging.getLogger(__name__)
log.addHandler(console)
log.setLevel(logging.INFO)

MAX_CONNECTION_RETRIES = 10
RETRY_WAIT = 5  # Number of sections to wait before retrying

DEFAULT_CHUNK_SIZE = 1000


class Command(BaseCommand):
    can_import_settings = True
    requires_migrations_checks = True

    def add_arguments(self, parser):
        parser.add_argument("--verbose",
                            action="store_true",
                            default=False,
                            help="Be very chatty and run logging at DEBUG")
        parser.add_argument("--chunk-size",
                            dest="chunk_size",
                            default=DEFAULT_CHUNK_SIZE,
                            type=int,
                            help="The number of records to batch process at once")

    def handle(self, *args, **options):
        if options['verbose']:
            log.setLevel(logging.DEBUG)
        self.index_all_images(chunk_size=options['chunk_size'])

    def index_all_images(self, chunk_size=DEFAULT_CHUNK_SIZE):
        """Index every record in the database as efficiently as possible"""
        es = search.init()
        search.Image.init()
        mapping = search.Image._doc_type.mapping
        mapping.save('openledger')

        batches = []
        retries = 0

        for db_image in models.Image.objects.all().iterator():
            try:
                log.debug("Indexing database record %s", db_image.identifier)
                image = search.db_image_to_index(db_image)
                if len(batches) > chunk_size:
                    helpers.bulk(es, batches)
                    log.debug("Pushed batch of %d records to ES", len(batches))
                    batches = []  # Clear the batch size
                else:
                    batches.append(image.to_dict(include_meta=True))
            except ConnectionError as e:
                if retries < MAX_CONNECTION_RETRIES:
                    log.warn("Got timeout, retrying with %d retries remaining", MAX_CONNECTION_RETRIES - retries)
                    es = init()
                    retries += 1
                    time.sleep(RETRY_WAIT)
                else:
                    raise

        helpers.bulk(es, batches)
