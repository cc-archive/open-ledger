import base64
import hashlib
import uuid

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager
from slugify import slugify
from sqlalchemy.dialects import postgresql
from sqlalchemy import event

from openledger import app

db = SQLAlchemy(app)
migrate = Migrate(app, db)
manager = Manager(app)
manager.add_command('db', MigrateCommand)

image_tags = db.Table('image_tags',
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id')),
    db.Column('image_id', db.Integer, db.ForeignKey('image.id')),
    db.Column('created_on', db.DateTime, server_default=db.func.now()),
    db.Column('updated_on', db.DateTime, server_default=db.func.now(), onupdate=db.func.now()),
)

class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    # A unique identifier that we assign on ingestion. This is "our" identifier.
    # See the event handler below for the algorithm to generate this value
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

    # The primary thumbnail URL for this image
#    thumbnail = db.Column(db.String(1000), nullable=True)

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

    # The author/creator/licensee, not that we'll know for sure
    creator = db.Column(db.String(2000), unique=False, index=True)

    # The URL to the creator's identity or profile, if known
    creator_url = db.Column(db.String(2000))

    # The title of the image, if available
    title = db.Column(db.String(2000), index=True)

    # Links to the tags table
    tags = db.relationship('Tag', secondary=image_tags, lazy='dynamic',
                           backref=db.backref('images', lazy='dynamic'))

    # Denormalized tags as an array, for easier syncing with Elasticsearch
    tags_list = db.Column(postgresql.ARRAY(db.String))

    created_on = db.Column(db.DateTime, server_default=db.func.now())
    updated_on = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

    def __repr__(self):
        return '<Image %r found at %r by %r>' % (self.identifier, self.url, self.creator)

@event.listens_for(Image, 'before_insert')
def event_create_identifier(mapper, connection, target):
    # This is a stable identifier that is derived from the URL
    target.identifier = create_identifier(target.url)

def create_identifier(url):
    """Create a unique, stable identifier for a URL"""
    m = hashlib.md5()
    m.update(bytes(url.encode('utf-8')))
    return base64.urlsafe_b64encode(m.digest()).decode('utf-8')

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


list_images = db.Table('list_images',
    db.Column('list_id', db.Integer, db.ForeignKey('list.id')),
    db.Column('image_id', db.Integer, db.ForeignKey('image.id')),
    db.Column('created_on', db.DateTime, server_default=db.func.now()),
    db.Column('updated_on', db.DateTime, server_default=db.func.now(), onupdate=db.func.now()),
)

class List(db.Model):
    """A user-generated curation of items"""
    id = db.Column(db.Integer, primary_key=True)

    images = db.relationship('Image', secondary=list_images, lazy='dynamic',
                           backref=db.backref('lists', lazy='dynamic'))

    # The title of the list. This is required, otherwise we have no way if identifying it
    title = db.Column(db.String(2000), index=True, nullable=False)

    # The displayable name of a creator, which can be anything
    creator_displayname = db.Column(db.String(2000), index=True)

    # The description of the list, which is optional
    description = db.Column(db.Text())

    # Whether this list is public/discoverable. May in the future be tied to a real
    # user when we have login
    is_public = db.Column(db.Boolean(), default=True)

    # The unique, URL-safe identifier for this list
    slug = db.Column(db.String(255), unique=True, index=True)

    created_on = db.Column(db.DateTime, server_default=db.func.now())
    updated_on = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

@event.listens_for(List, 'before_insert')
def event_create_slug(mapper, connection, target):
    uniquish = str(uuid.uuid4())[:8]
    target.slug = create_slug([target.title, uniquish])

def create_slug(el):
    """For the list of items el, create a unique slug out of them"""
    return '-'.join([slugify(str(i)) for i in el])


if __name__ == '__main__':
    # pass through to the database management commands
    manager.run()
