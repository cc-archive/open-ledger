from flask_sqlalchemy import SQLAlchemy

from openledger import app

db = SQLAlchemy(app)

class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    google_imageid = db.Column(db.String(80), unique=True)
    original_landing_url = db.Column(db.String(1000), unique=True)
    image_url = db.Column(db.String(1000), unique=True)
    license_url = db.Column(db.String(120), unique=False)
    author_url = db.Column(db.String(1000), unique=False)
    author = db.Column(db.String(1000), unique=False)
    title = db.Column(db.String(1000), unique=False)

    def __repr__(self):
        return '<Image %r by %r>' % (self.image_url, self.author)
