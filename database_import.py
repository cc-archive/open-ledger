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
log.setLevel(logging.INFO)

TAG_CONFIDENCE_THRESHOLD = 0.5  # Don't import tags with confidence levels lower than this

def import_images_from_openimages(filename):
    """Import image records from the `open-images` dataset"""
    fields = ('ImageID', 'Subset', 'OriginalURL', 'OriginalLandingURL', 'License',
              'AuthorProfileURL', 'Author', 'Title')
    log.debug("Creating database schema if it doesn't exist...")
    with app.app_context():
        db.create_all()
        with open(filename) as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                try:
                    if not Image.query.filter_by(foreign_identifier=row['ImageID']).first():
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

                        log.debug("Adding image %s", row['ImageID'])
                        db.session.add(image)
                        db.session.commit()
                    else:
                        log.debug("Skipping existing image %s", row['ImageID'])
                except IntegrityError as e:
                    db.session.rollback()
                    log.debug(e)

def import_images_tags_from_openimages(filename):
    """Import tag/image relationships from the `open-images` dataset"""
    with app.app_context():
        db.create_all()
        with open(filename) as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                image_id = row['ImageID']
                tag_id = row['LabelName']
                confidence = row['Confidence']
                if float(confidence) < TAG_CONFIDENCE_THRESHOLD:
                    continue
                img = Image.query.filter_by(foreign_identifier=image_id).first()
                tag = Tag.query.filter_by(foreign_identifier=tag_id).first()
                if tag and img:
                    log.debug("Adding tag %s to image %s ", tag.name, img.title)
                    img.tags.append(tag)
            db.session.commit()

def import_tags_from_openimages(filename):
    """Import tag names from the `open-images` dataset"""
    with app.app_context():
        db.create_all()
        with open(filename) as fh:
            reader = csv.reader(fh)
            for row in reader:
                try:
                    tag = Tag()
                    tag.foreign_identifier = row[0].strip()
                    tag.name = row[1].strip()
                    tag.source = 'openimages'
                    log.debug("Adding tag %s", tag.name)
                    db.session.add(tag)
                    db.session.commit()
                except IntegrityError as e:
                    db.session.rollback()
                    log.debug(e)

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
    (fh, datafile) = tempfile.mkstemp()
    s3.download_file(Bucket=bucket_name, Key=filename, Filename=datafile)
    return datafile

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
    parser.add_argument("--verbose",
                        action="store_true",
                        default=False,
                        help="Be very chatty and run logging at DEBUG")
    args = parser.parse_args()

    if args.verbose:
        log.setLevel(logging.DEBUG)

    # Collect the input files from the local filesystem or S3
    delete_source_when_done = False

    if args.filesystem == 's3':
        delete_source_when_done = True  # This will be a temporary file
        filename = download_from_s3(args.filepath, args.bucket_name, args.source)
    else:
        filename = args.filepath

    try:
        # Process the filetype with the correct handler
        if args.source == 'openimages' and args.datatype == "images":
            import_images_from_openimages(filename)
        elif args.source == 'openimages' and args.datatype == "tags":
            import_tags_from_openimages(filename)
        elif args.source == 'openimages' and args.datatype == "image-tags":
            import_images_tags_from_openimages(filename)

    except:
        raise

    finally:
        if delete_source_when_done:
            os.remove(filename)
