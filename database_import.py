import argparse
import csv
import logging
import tempfile

import boto3
import botocore
from sqlalchemy.exc import IntegrityError

from openledger.models import db, Image

console = logging.StreamHandler()

log = logging.getLogger(__name__)
log.addHandler(console)
log.setLevel(logging.DEBUG)

def import_from_open_images(fh):
    fields = ('ImageID', 'Subset', 'OriginalURL', 'OriginalLandingURL', 'License',
              'AuthorProfileURL', 'Author', 'Title')
    log.info("Creating database schema if it doesnt' exist...")
    db.create_all()
    reader = csv.DictReader(csvfile)
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
            log.info("Adding image ", row['ImageID'])
        except IntegrityError:
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
    obj = s3.get_object(Bucket=bucket_name, Key=filename)
    data = obj['Body']
    with tempfile.TemporaryFile() as fp:
        fp.write(data.read())
        fp.seek(0)
        if source == 'openimages':
            import_from_open_images(fp)

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
    if args.source == 'openimages':
        with open(args.filepath) as fh:
            import_from_open_images(fh)
