import argparse
import csv
import logging
import os
import tempfile
import uuid

import boto3
import botocore
from sqlalchemy.exc import IntegrityError

from openledger.models import db, Image, Tag
from openledger import app

console = logging.StreamHandler()

log = logging.getLogger(__name__)
log.addHandler(console)
log.setLevel(logging.DEBUG)

def import_images_from_openimages(filename):
    """Import image records from the `open-images` dataset"""
    fields = ('ImageID', 'Subset', 'OriginalURL', 'OriginalLandingURL', 'License',
              'AuthorProfileURL', 'Author', 'Title')
    log.info("Creating database schema if it doesn't exist...")
    with app.app_context():
        db.create_all()
        with open(filename) as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                try:
                    with db.session.begin_nested():
                        image = Image()
                        image.identifier = row['OriginalMD5']  # We get a nice unique, stable value, let's use it
                        image.foreign_identifier = row['ImageID']
                        image.url = row['OriginalURL']
                        image.foreign_landing_url = row['OriginalLandingURL']
                        image.license = 'BY'
                        image.provider = 'flickr'
                        image.source = 'openimages'
                        image.license_version = '2.0'
                        image.creator_url = row['AuthorProfileURL']
                        image.creator = row['Author']
                        image.title = row['Title']
                        image.filesize = row['OriginalSize']

                        log.info("Adding image %s", row['ImageID'])
                        db.session.merge(image)
                except Exception as e:
                    log.warn(e)
            db.session.commit()

def import_tags_from_openimages(filename):
    """Import tag names from the `open-images` dataset"""
    with app.app_context():
        db.create_all()
        with open(filename) as fh:
            reader = csv.reader(fh)
            for row in reader:
                try:
                    with db.session.begin_nested():
                        tag = Tag()
                        tag.mid = row[0].strip()
                        tag.tag = row[1].strip()
                        tag.source = 'openimages'
                        log.info("Adding tag %s", tag.mid)
                        db.session.merge(tag)
                except Exception as e:
                    log.warn(e)
            db.session.commit()

def download_from_s3(filename, bucket_name, source):
    """Download the named file from the CC openledger bucket to begin processing it.
    Returns the name of the temporary file containing the data."""
    # May need to change this to support getting the access key id from the OS env
    log.info("Getting file %s from S3 bucket %s for source %s", filename, bucket_name, source)
    try:
        session = boto3.Session(profile_name='cc-openledger')
    except botocore.exceptions.ProfileNotFound:
        session = boto3.Session()
    s3 = session.client('s3')
    f = tempfile.NamedTemporaryFile()
    s3.download_file(Bucket=bucket_name, Key=filename, Filename=f.name)
    return f.name

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("filepath",
                        help="The complete file path (or s3 key) for the provider")
    parser.add_argument("source",
                        help="The name of the source for this dataset, e.g. openimages")
    parser.add_argument("datatype",
                        help="The datatype to be loaded: 'images', 'tags', or 'image-tags'")
    parser.add_argument("--bucket",
                        dest="bucket_name",
                        default="cc-openledger-sources",
                        help="The S3 bucket name"),
    parser.add_argument("--filesystem",
                        dest="filesystem",
                        default="local",
                        help="The name of the filesystem: local or s3")
    args = parser.parse_args()

    # Collect the input files from the local filesystem or S3
    if args.filesystem == 's3':
        filename = download_from_s3(args.filepath, args.bucket_name, args.source)
    else:
        filename = args.filepath

    # Process the filetype with the correct handler
    if args.source == 'openimages' and args.datatype == "images":
        import_images_from_openimages(filename)
    elif args.source == 'openimages' and args.datatype == "tags":
        import_tags_from_openimages(filename)
    elif args.source == 'openimages' and args.datatype == "image-tags":
        import_images_tags_from_openimages(filename)
