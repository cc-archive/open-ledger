import sys
import csv

from openledger.models import db, Image

filename = sys.argv[1]
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

    db.session.commit()
