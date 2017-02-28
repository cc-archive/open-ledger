import itertools
import logging
import os
import tempfile

import boto3
import botocore

from django.core.management.base import BaseCommand, CommandError

from imageledger.handlers import handler_rijks, handler_nypl, handler_500px, \
    handler_wikimedia, handler_met, handler_europeana

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

DEFAULT_CHUNK_SIZE = 1000
DEFAULT_NUM_THREADS = 4

class Command(BaseCommand):
    can_import_settings = True
    requires_migrations_checks = True

    current_handlers = ('rijks', 'nypl', '500px', 'wikimedia', 'met', 'europeana')

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
        parser.add_argument("--bucket",
                            dest="bucket_name",
                            default="cc-openledger-sources",
                            help="The S3 bucket name"),
        parser.add_argument("--max-results",
                            dest="max_results",
                            default=5000,
                            type=int,
                            help="The maximum number of results to retrieve from the API cycle")
        parser.add_argument("--from-file",
                            dest="from_file",
                            help="A raw import file that will be passed to the handler for use instead of an API")
        parser.add_argument("--num-threads",
                            dest="num_threads",
                            default=DEFAULT_NUM_THREADS,
                            type=int,
                            help="Number of threads to run loader in (only valid for `met`)")

    def handle(self, *args, **options):
        added = 0
        if options['verbose']:
            log.setLevel(logging.DEBUG)
        if options['handler'] not in self.current_handlers:
            raise CommandError("Handler must be one of the values in `current_handlers`")
        if options['handler'] == 'rijks':
            added = handler_rijks.insert_image(walk_func=handler_rijks.walk,
                                               serialize_func=handler_rijks.serialize,
                                               chunk_size=options['chunk_size'],
                                               max_results=options['max_results'])
        elif options['handler'] == '500px':
            added = handler_500px.insert_image(walk_func=handler_500px.walk,
                                               serialize_func=handler_500px.serialize,
                                               chunk_size=options['chunk_size'],
                                               max_results=options['max_results'])
        elif options['handler'] == 'wikimedia':
            added = handler_wikimedia.insert_image(walk_func=handler_wikimedia.walk,
                                                   serialize_func=handler_wikimedia.serialize,
                                                   chunk_size=options['chunk_size'],
                                                   max_results=options['max_results'])
        elif options['handler'] == 'nypl':
            if options.get('bucket_name'):
                file_dir = download_from_s3(options['from_file'], options['bucket_name'])
            else:
                file_dir = options['from_file']
            added = handler_nypl.insert_image(options['chunk_size'], options['max_results'], from_file=file_dir)
        elif options['handler'] == 'met':
            handler_met.walk(num_threads=options['num_threads'])
        elif options['handler'] == 'europeana':
            added = handler_europeana.insert_image(walk_func=handler_europeana.walk,
                                                   serialize_func=handler_europeana.serialize,
                                                   chunk_size=options['chunk_size'],
                                                   max_results=options['max_results'])


        log.info("Successfully added %d images out of max %d attempted", added, options['max_results'])

def download_from_s3(filename, bucket_name):
    """Download the named file from the CC openledger bucket to begin processing it.
    Returns the name of the temporary file containing the data."""
    log.info("Getting file %s from S3 bucket %s ", filename, bucket_name)
    try:
        session = boto3.Session(profile_name='cc-openledger')
    except botocore.exceptions.ProfileNotFound:
        session = boto3.Session()
    s3 = session.client('s3')
    (fh, datafile) = tempfile.mkstemp()
    s3.download_file(Bucket=bucket_name, Key=filename, Filename=datafile)
    return datafile
