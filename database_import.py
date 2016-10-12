import csv
import argparse


from sqlalchemy.exc import IntegrityError

from openledger.models import db, Image

def import_from_open_images(filename):
    fields = ('ImageID', 'Subset', 'OriginalURL', 'OriginalLandingURL', 'License',
              'AuthorProfileURL', 'Author', 'Title')

    with open(filename) as csvfile:
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
                print("Adding image ", row['ImageID'])
            except IntegrityError:
                db.session.rollback()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--open-images-path",
                        dest="openimages_path",
                        help="The location of the Google Open Images csv file")
    parser.add_argument("--flickr-100m-path",
                        dest="flickr100m_path",
                        help="The location of the Flickr 100M tsv directory")
    args = parser.parse_args()
    if args.openimages_path:
        import_from_open_images(args.openimages_path)
