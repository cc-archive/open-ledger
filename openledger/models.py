from flask_sqlalchemy import SQLAlchemy

from openledger import app

db = SQLAlchemy(app)

tags = db.Table('tags',
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id')),
    db.Column('image_id', db.Integer, db.ForeignKey('image.id')),
)

class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    google_imageid = db.Column(db.String(80), unique=True, index=True)
    original_landing_url = db.Column(db.String(1000), unique=True)
    image_url = db.Column(db.String(1000), unique=True)
    license_url = db.Column(db.String(120), unique=False)
    author_url = db.Column(db.String(1000), unique=False)
    author = db.Column(db.String(1000), unique=False, index=True)
    title = db.Column(db.String(1000), unique=False, index=True)
    tags = db.relationship('Tag', secondary=tags, lazy='dynamic',
                           backref=db.backref('images', lazy='dynamic'))
    def __repr__(self):
        return '<Image %r by %r>' % (self.image_url, self.author)

class Tag(db.Model):
    """A word or phrase associated with this image"""
    id = db.Column(db.Integer, primary_key=True)
    mid = db.Column(db.String(255))
    tag = db.Column(db.String(1000), index=True)
    source = db.Column(db.String(255), index=True)
