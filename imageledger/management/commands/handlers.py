import itertools
import logging
import os
import tempfile

from django.core.management.base import BaseCommand, CommandError

from imageledger.handlers import handler_rijks

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

DEFAULT_CHUNK_SIZE = 1000

class Command(BaseCommand):
    can_import_settings = True
    requires_migrations_checks = True

    current_handlers = ('rijks',)

    def add_arguments(self, parser):
        parser.add_argument("handler",
                            help="The handler to be loaded. Currently available: {}".format(', '.join(self.current_handlers)))
        parser.add_argument("--verbose",
                            action="store_true",
                            default=False,
                            help="Be very chatty and run logging at DEBUG")
        parser.add_argument("--chunk-size",
                            dest="chunk_size",
                            default=DEFAULT_CHUNK_SIZE,
                            type=int,
                            help="The number of records to batch process at once")
        parser.add_argument("--max-results",
                            dest="max_results",
                            default=5000,
                            type=int,
                            help="The maximum number of results to retrieve from the API cycle")

    def handle(self, *args, **options):
        if options['verbose']:
            log.setLevel(logging.DEBUG)
        if options['handler'] not in self.current_handlers:
            raise CommandError("Handler must be one of the values in `current_handlers`")
        if options['handler'] == 'rijks':
            added = handler_rijks.insert_image(options['chunk_size'], options['max_results'])
            log.info("Successfully added %d images out of max %d attempted", added, options['max_results'])
