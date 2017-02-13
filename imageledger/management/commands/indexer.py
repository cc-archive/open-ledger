from collections import namedtuple
import itertools
import logging
import os
import time
from multiprocessing.dummy import Pool
import multiprocessing
import uuid

from elasticsearch import helpers
import elasticsearch
from elasticsearch_dsl import Index
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
import requests

from imageledger import models, search

console = logging.StreamHandler()
log = logging.getLogger(__name__)
log.addHandler(console)
log.setLevel(logging.INFO)

MAX_CONNECTION_RETRIES = 50
RETRY_WAIT = 5  # Number of sections to wait before retrying

DEFAULT_CHUNK_SIZE = 1000
DEFAULT_NUM_ITERATIONS = 10000
DEFAULT_NUM_THREADS = 4

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
        parser.add_argument("--num-iterations",
                            dest="num_iterations",
                            default=DEFAULT_NUM_ITERATIONS,
                            type=int,
                            help="The number of times to loop through `chunk_size` records")
        parser.add_argument("--num-threads",
                            dest="num_threads",
                            default=DEFAULT_NUM_THREADS,
                            type=int,
                            help="The number of threads to start up at once")

    def handle(self, *args, **options):
        if options['verbose']:
            log.setLevel(logging.DEBUG)
        self.index_all_images(chunk_size=options['chunk_size'],
                              num_iterations=options['num_iterations'],
                              num_threads=options['num_threads']
                              )


    def index_all_images(self, chunk_size=DEFAULT_CHUNK_SIZE, num_iterations=DEFAULT_NUM_ITERATIONS,
                         num_threads=DEFAULT_NUM_THREADS):
        """Index every record in the database with a server-side cursor"""
        index = Index(settings.ELASTICSEARCH_INDEX)
        if not index.exists():
            log.info("Creating new index %s", settings.ELASTICSEARCH_INDEX)
            search.Image.init()
            mapping = search.Image._doc_type.mapping
            mapping.save(settings.ELASTICSEARCH_INDEX)
            log.info("Done creating new index")

        with Pool(num_threads) as pool:
            starts = [i * chunk_size for i in range(0, num_iterations)]
            pool.starmap(do_index, zip(starts, itertools.repeat(chunk_size, len(starts))))


def do_index(start, chunk_size):
    end = start + chunk_size + 1
    batches = []
    retries = 0
    try:
        es = search.init(timeout=2000)
        if not settings.DEBUG:
            es.cluster.health(wait_for_status='green', request_timeout=2000)

    except (requests.exceptions.ReadTimeout, elasticsearch.exceptions.TransportError) as e:
        log.warn(e)
        log.warn("Skipping batch and retrying after wait")
        time.sleep(RETRY_WAIT)
        return

    log.debug("Starting index in range from %d to %d...", start, end)

    qs = models.Image.objects.filter(removed_from_source=False, id__gt=start).order_by('id')[0:chunk_size]
    #qs = models.Image.objects.filter(removed_from_source=False).order_by('id')[start:end]
    for db_image in server_cursor_query(qs, chunk_size=chunk_size):
        log.debug("Indexing database record %s", db_image.identifier)
        image = search.db_image_to_index(db_image)
        try:
            if len(batches) >= chunk_size:
                if not settings.DEBUG:
                    log.debug("Waiting for green status...")
                    es.cluster.health(wait_for_status='green', request_timeout=2000)
                helpers.bulk(es, batches)
                log.debug("Pushed batch of %d records to ES", len(batches))
                batches = []  # Clear the batch size
            else:
                batches.append(image.to_dict(include_meta=True))
        except (requests.exceptions.ReadTimeout,
                elasticsearch.exceptions.TransportError,
                elasticsearch.helpers.BulkIndexError) as e:
            if retries < MAX_CONNECTION_RETRIES:
                log.warn("Got timeout: retrying with %d retries remaining", MAX_CONNECTION_RETRIES - retries)
                retries += 1
                time.sleep(RETRY_WAIT)
            else:
                raise
    helpers.bulk(es, batches)

def server_cursor_query(queryset, cursor_id=0, chunk_size=DEFAULT_CHUNK_SIZE):
    connection.cursor()

    compiler = queryset.query.get_compiler(using=queryset.db)
    sql, params = compiler.as_sql()

    model = compiler.klass_info['model']
    select_fields = compiler.klass_info['select_fields']
    fields = [field[0].target.attname
              for field in compiler.select[select_fields[0]:select_fields[-1] + 1]]

    cursor_name = 'cursor-large-%d' % cursor_id
    cursor = connection.connection.cursor(name=cursor_name)
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

def grouper_it(n, iterable):
    it = iter(iterable)
    while True:
        chunk_it = itertools.islice(it, n)
        try:
            first_el = next(chunk_it)
        except StopIteration:
            return
        yield itertools.chain((first_el,), chunk_it)
