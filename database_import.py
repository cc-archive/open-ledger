import argparse
import csv
import logging
import os
import tempfile

import boto3
import botocore
from sqlalchemy.exc import IntegrityError

from openledger.models import db, Image

console = logging.StreamHandler()

log = logging.getLogger(__name__)
log.addHandler(console)
log.setLevel(logging.DEBUG)

def import_from_open_images(filename):
    fields = ('ImageID', 'Subset', 'OriginalURL', 'OriginalLandingURL', 'License',
              'AuthorProfileURL', 'Author', 'Title')
    log.info("Creating database schema if it doesn't exist...")
    db.create_all()
    with open(filename) as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            image = Image()
            image.google_imageid = row['ImageID']
            image.image_url = row['OriginalURL']
            image.original_landing_url = row['OriginalLandingURL']
            image.license_url = row['License']
            image.author_url = row['AuthorProfileURL']
            image.author = row['Author']
            image.title = row['Title']
            db.session.add(image)
            try:
                db.session.commit()
                log.info("Adding image %s", row['ImageID'])
            except IntegrityError:
                log.debug("Skipping already-loaded image %s", row['ImageID'])
                db.session.rollback()

def download_from_s3(filename, bucket_name, source):
    """Download the named file from the CC openledger bucket to begin processing it"""
    # May need to change this to support getting the access key id from the OS env
    log.info("Getting file %s from S3 bucket %s for source %s", filename, bucket_name, source)
    try:
        session = boto3.Session(profile_name='cc-openledger')
    except botocore.exceptions.ProfileNotFound:
        session = boto3.Session()
    s3 = session.client('s3')
    f = tempfile.NamedTemporaryFile()
    s3.download_file(Bucket=bucket_name, Key=filename, Filename=f.name)
    if source == 'openimages':
        import_from_open_images(f.name)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("filepath",
                        help="The complete file path (or s3 key) for the provider")
    parser.add_argument("source",
                        help="The name of the source for this dataset, e.g. openimages")
    parser.add_argument("--bucket",
                        dest="bucket_name",
                        default="cc-openledger-sources",
                        help="The S3 bucket name"),
    parser.add_argument("--filesystem",
                        dest="filesystem",
                        default="local",
                        help="The name of the filesystem: local or s3")
    args = parser.parse_args()
    if args.filesystem == 's3':
        download_from_s3(args.filepath, args.bucket_name, args.source)
    elif args.source == 'openimages':
        import_from_open_images(args.filepath)
