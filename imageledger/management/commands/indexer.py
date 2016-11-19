from collections import namedtuple
import logging

from elasticsearch import helpers
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction

from imageledger import models, search

log = logging.getLogger(__name__)

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

    def server_cursor_query(self, queryset, chunk_size=DEFAULT_CHUNK_SIZE):
        compiler = queryset.query.get_compiler(using=queryset.db)
        sql, params = compiler.as_sql()

        model = compiler.klass_info['model']
        select_fields = compiler.klass_info['select_fields']
        fields = [field[0].target.attname
                  for field in compiler.select[select_fields[0]:select_fields[-1] + 1]]

        cursor = connection.connection.cursor(name='gigantic_cursor')
        with transaction.atomic(savepoint=False):
            cursor.execute(sql, params)

            while True:
                rows = cursor.fetchmany(chunk_size)
                if not rows:
                    break
                for row in rows:
                    DBObj = namedtuple('DBObj', fields)
                    obj = DBObj(*row[select_fields[0]:select_fields[-1] + 1])
                    yield obj
                    #yield fields
                    #obj = model.from_db(queryset.db, fields, row[select_fields[0]:select_fields[-1] + 1])
                    #yield obj

    def index_all_images(self, chunk_size=DEFAULT_CHUNK_SIZE):
        """Index every record in the database as efficiently as possible"""
        es = search.init()
        search.Image.init()
        mapping = search.Image._doc_type.mapping
        mapping.save('openledger')
        connection.cursor()

        batches = []
        retries = 0
        completed = 0

        # Make use of the auto-incrementing ID
        total = models.Image.objects.count()
        log.info("Will index %d records", total)

        for pk in range(0, total):
            try:
                db_image = models.Image.objects.get(pk=pk)
            except models.Image.DoesNotExist:
                continue
            # log.debug("Indexing database record %s", db_image.identifier)
            image = search.db_image_to_index(db_image)
            try:
                 if len(batches) > chunk_size:
                     helpers.bulk(es, batches)
                     log.debug("Pushed batch of %d records to ES", len(batches))
                     completed += len(batches)
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
        completed += len(batches)
        log.info("Finished with %d batches completed", completed)
