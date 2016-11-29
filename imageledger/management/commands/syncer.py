from collections import namedtuple
import itertools
import logging

from elasticsearch import helpers
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction

from imageledger import models, search

console = logging.StreamHandler()
log = logging.getLogger(__name__)
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
        parser.add_argument("--with-fingerprinting",
                            dest="with_fingerprinting",
                            action="store_true",
                            help="Whether to run the expensive perceptual hash routine as part of syncing")

    def handle(self, *args, **options):
        if options['verbose']:
            log.addHandler(console)
            log.setLevel(logging.DEBUG)
        self.sync_all_images(chunk_size=options['chunk_size'], with_fingerprinting=options['with_fingerprinting'])

    def sync_all_images(self, chunk_size=DEFAULT_CHUNK_SIZE, with_fingerprinting=False, num_iterations=1000):
        """Sync all of the images, sorting from least-recently-synced"""
        count = 0
        while count < num_iterations:
            imgs = models.Image.objects.all().order_by('-last_synced_with_source')[0:chunk_size]
            for img in imgs:
                img.sync(attempt_perceptual_hash=with_fingerprinting)
                count += 1
