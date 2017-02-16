from collections import namedtuple
import itertools
import logging
import os
import datetime

from elasticsearch import helpers
import elasticsearch
from elasticsearch_dsl import Index, Search
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

# Remap an old index to a new one (presumably because mappings changed)

from imageledger import search

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
        parser.add_argument("--force",
                            action="store_true",
                            default=False,
                            help="Force deleting an old index if it exists—only on newindex!")
        parser.add_argument("oldindex",
                            help="The name of the old index that we'll draw data from")
        parser.add_argument("newindex",
                            help="The name of the new index.")

    def handle(self, *args, **options):
        if options['verbose']:
            log.setLevel(logging.DEBUG)

        es = search.init_es(timeout=2000)

        oldindex = Index(options['oldindex'])
        client = elasticsearch.client.IndicesClient(es)
        # Create the new index
        newindex = Index(options['newindex'])
        newindex.doc_type(search.Image)

        try:
            newindex.create()
        except elasticsearch.exceptions.RequestError as e:
            if options['force']:
                log.warn("Trying to delete previously-created new index %s", options['newindex'])
                newindex.delete()
                newindex.create()
            else:
                raise e
        log.info("Done creating new index %s", options['newindex'])

        log.info("Copying data on %s to %s", options['oldindex'], options['newindex'])

        # Would love to use ES native reindex() but AWS's service doesn't support it :(
        elasticsearch.helpers.reindex(es, options['oldindex'], options['newindex'])


        # Wait for it to be happy
        if not settings.DEBUG:
            es.cluster.health(wait_for_status='green', request_timeout=2000)


        # Is the value of 'oldindex' an alias or a real index?
        if client.exists_alias(name=settings.ELASTICSEARCH_INDEX):
            log.info("Confirmed that value of %s is an alias and not a real index" % options['oldindex'])
            alias_move = """{
                "actions" : [
                    { "remove" : { "index" : "%s", "alias" : "%s" } },
                    { "add" : { "index" : "%s", "alias" : "%s" } }
                ]
            }""" % (options['oldindex'], settings.ELASTICSEARCH_INDEX, options['newindex'], settings.ELASTICSEARCH_INDEX)
            client.update_aliases(alias_move)

        elif client.exists(options['oldindex']):
            log.info("%s is a real index and not an alias, fixing" % options['oldindex'])

            # Delete the old index
            log.info("Deleting %s -- this will cause some downtime", options['oldindex'])
            oldindex.delete()
            client.put_alias(options['newindex'], settings.ELASTICSEARCH_INDEX)

        # Confirm number of documents in current settings
        s = Search()
        response = s.execute()
        log.info("%d results available in %s" % (response.hits.total, settings.ELASTICSEARCH_INDEX))
