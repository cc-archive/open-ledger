import logging

from openledger import models

log = logging.getLogger(__name__)

def get_list(slug):
    lst = models.List.query.filter(models.List.slug==slug).first()
    if not lst:
        return None
    return lst

def get_lists(title=None):
    lsts = models.List.query.filter(models.List.title.contains(title))
    return lsts

def delete_list(slug):
    lst = models.List.query.filter(models.List.slug==slug).first()
    if not lst:
        return None
    models.db.session.delete(lst)
    models.db.session.commit()
    return lst

def update_list(slug, image_identifiers=[]):
    """Update a List, replacing the set of images with the supplied collection"""
    lst = models.List.query.filter(models.List.slug==slug).first()
    if not lst:
        return None

    if len(image_identifiers) > 0:
        images = models.Image.query.filter(models.Image.identifier.in_(image_identifiers))
        lst.images = images

    models.db.session.add(lst)
    models.db.session.commit()
    return lst

def create_list(title, image_identifiers=[]):
    """Create a List, populating it with the set of images supplied"""
    lst = models.List(title=title)

    if len(image_identifiers) > 0:
        images = models.Image.query.filter(models.Image.identifier.in_(image_identifiers))
        lst.images = images

    models.db.session.add(lst)
    models.db.session.commit()
    return lst

def add_image_to_list(slug, image_identifier=None):
    """Add an image to an existing List, without modifying other images already supplied. Returns the image added."""
    lst = models.List.query.filter(models.List.slug==slug).first()
    if not lst:
        return None
    image = models.Image.query.filter(models.Image.identifier==image_identifier).first()
    if image:
        lst.images.append(image)
        models.db.session.add(lst)
        models.db.session.commit()
    return image
