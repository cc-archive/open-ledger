import sys
import csv

from sqlalchemy.exc import IntegrityError

from openledger.models import *

tag_file = sys.argv[1]
labels_file = sys.argv[2]

with open(tag_file) as csvfile:
    db.create_all()
    reader = csv.reader(csvfile)
    for row in reader:
        # Skip existing ones
        if not Tag.query.filter_by(mid=row[0]).first():
            print("Adding tag ", row[1])
            tag = Tag()
            tag.mid = row[0].strip()
            tag.tag = row[1].strip()
            tag.source = 'openimages'
            db.session.add(tag)
    db.session.commit()

with open(labels_file) as csvfile:
    reader = csv.reader(csvfile)
    for row in reader:
        image_id = row[0]
        tags = row[2:]
        img = Image.query.filter_by(google_imageid=image_id).first()
        tag_objs = []
        for tag in tags:
            confidence, mid = tag.split(':')
            if float(confidence) < 0.5:
                continue
            tag = Tag.query.filter_by(mid=mid).first()
            if tag:
                print("Adding tag ", tag.tag, " to image ", img.title)
                img.tags.append(tag)
    db.session.commit()
