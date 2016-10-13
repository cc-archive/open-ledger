from flask_sqlalchemy import SQLAlchemy

from openledger import app

db = SQLAlchemy(app)

image_tags = db.Table('image_tags',
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id')),
    db.Column('image_id', db.Integer, db.ForeignKey('image.id')),
    db.Column('created_on', db.DateTime, server_default=db.func.now()),
    db.Column('updated_on', db.DateTime, server_default=db.func.now(), onupdate=db.func.now()),
)

class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    # A unique identifier that we assign on ingestion. This is "our" identifier.
    # It's a UUID, typically
    # FIXME future improvement could mean making it idempotent, maybe based on
    # the source URL?
    identifier = db.Column(db.String(255), index=True, unique=True)

    # The perceptual hash we generate from the source image TODO
    perceptual_hash = db.Column(db.String(255), unique=True, index=True)

    # The provider of the data, typically a partner like Flickr or 500px
    provider = db.Column(db.String(80), index=True)

    # The source of the data, meaning a particular dataset. Source and provider
    # can be different: the Google Open Images dataset is source=openimages,
    # but provider=Flickr (since all images are Flickr-originated)
    source = db.Column(db.String(80), index=True)

    # The identifier that was defined by the source or provider. This may need
    # to be extended to support multiple values when we begin to reconcile duplicates
    foreign_identifier = db.Column(db.String(80), unique=True, index=True)

    # The entry point URL that we got from the external source, such as the
    # HTTP referrer, or the landing page recorded by the provider/source
    foreign_landing_url = db.Column(db.String(1000))

    # The actual URL to the primary resolution of the image
    # Note that this is unique!
    url = db.Column(db.String(1000), unique=True, nullable=False)

    # Image dimensions, if available
    width = db.Column(db.Integer)
    height = db.Column(db.Integer)

    # The original filesize, if available, in bytes
    filesize = db.Column(db.Integer)

    # The license string as specified in licenses.py
    # This field is _required_, we have no business having a record of an image
    # if we don't know its license
    license = db.Column(db.String(50), nullable=False)

    # The license version as a string, optional as we may not have good metadata
    # This is a string to accommodate potential oddball/foreign values, but normally
    # should be a decimal like "2.0"
    license_version = db.Column(db.String(25))

    # The author/creator/licensee, not that we'll know
    creator = db.Column(db.String(2000), unique=False, index=True)

    # The URL to the creator's identity or profile, if known
    creator_url = db.Column(db.String(2000))

    # The title of the image, if available
    title = db.Column(db.String(2000), index=True)

    # Links to the tags table
    tags = db.relationship('Tag', secondary=image_tags, lazy='dynamic',
                           backref=db.backref('images', lazy='dynamic'))

    created_on = db.Column(db.DateTime, server_default=db.func.now())
    updated_on = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

    def __repr__(self):
        return '<Image %r by %r>' % (self.image_url, self.author)

class Tag(db.Model):
    """A word or phrase associated with this image"""
    id = db.Column(db.Integer, primary_key=True)

    # Foreign identifier, such as a Google Open Images 'mid'
    foreign_identifier = db.Column(db.String(255))

    # The human-readable name of the tag
    name = db.Column(db.String(1000), index=True)

    # The source of the data (e.g. 'openimages')
    source = db.Column(db.String(255), index=True)

    created_on = db.Column(db.DateTime, server_default=db.func.now())
    updated_on = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
