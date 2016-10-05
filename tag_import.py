import sys
import csv

from openledger.models import db, Tag

filename = sys.argv[1]

with open(filename) as csvfile:
    db.create_all()
    reader = csv.reader(csvfile)
    for row in reader:
        tag = Tag()
        tag.mid = row[0]
        tag.tag = row[1]
        tag.source = 'openimages'
        db.session.add(tag)
    db.session.commit()
