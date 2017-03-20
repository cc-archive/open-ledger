import json
import logging

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from elasticsearch_dsl import Search, Q
from imageledger import models, search

# This is a catch-all management command for one-off queries that need to be executed
# in the Django environment. It's expected that most of these functions will be short-lived,
# but are retained in source code for future reference.

console = logging.StreamHandler()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

class Command(BaseCommand):
    can_import_settings = True
    requires_migrations_checks = True

    def add_arguments(self, parser):
        parser.add_argument("--verbose",
                            action="store_true",
                            default=False,
                            help="Be very chatty and run logging at DEBUG")
        parser.add_argument("func",
                            help="The function to be run")

    def handle(self, *args, **options):
        if options['verbose']:
            log.setLevel(logging.DEBUG)
        getattr(self, options['func'])()


    def correct_orphan_records(self, provider='europeana', end=None):
        """[#185] Delete records from the search engine which aren't found in the database"""
        s = Search()
        q = Q('term', provider=provider)
        s = s.query(q)
        response = s.execute()
        total = response.hits.total
        # A file extracted from the production database listing all of the europeana identifiers
        identifier_file = '/tmp/europeana-identifiers.json'
        db_identifiers = set(json.load(open(identifier_file)))
        total_in_db = len(db_identifiers)
        log.info("Using search engine instance %s", settings.ELASTICSEARCH_URL)
        log.info("Total records: %d (search engine), %d (database) [diff=%d]", total, total_in_db, total - total_in_db)
        deleted_count = 0
        for r in s.scan():
            if r.identifier not in db_identifiers:
                img = search.Image.get(id=r.identifier)
                log.debug("Going to delete image %s", img)
                deleted_count += 1
        log.info("Deleted %d from search engine", deleted_count)
