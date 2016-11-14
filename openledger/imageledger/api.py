import logging

from imageledger import models

log = logging.getLogger(__name__)

def get_list(slug):
    lst = models.List.objects.filter(slug=slug).first()
    if not lst:
        return None
    return lst

def get_lists(title=None, match_method='contains'):
    """Get a list matching title. If `match_method` is 'contains', finds
    matches anywhere in the title. If 'startswith', will match only
    when starting with that string (as in autocomplete)"""

    if match_method == 'startswith':
        return models.List.objects.filter(title__startswith=title)
    else:
        return models.List.objects.filter(title__contains=title)


def delete_list(slug):
    lst = models.List.objects.filter(slug=slug).first()
    if not lst:
        return None
    lst.delete()
    return lst

def update_list(slug, image_identifiers=[]):
    """Update a List, replacing the set of images with the supplied collection"""
    lst = models.List.objects.filter(slug=slug).first()
    if not lst:
        return None
    if len(image_identifiers) > 0:
        lst.images.clear()
        images = models.Image.objects.filter(identifier__in=image_identifiers)
        for img in images:
            lst.images.add(img)
        lst.save()
    return lst

def create_list(title, image_identifiers=[]):
    """Create a List, populating it with the set of images supplied"""
    lst = models.List.objects.create(title=title)

    if len(image_identifiers) > 0:
        images = models.Image.objects.filter(identifier__in=image_identifiers)
        for img in images:
            lst.images.add(img)
        lst.save()
    return lst

def add_image_to_list(slug, image_identifier=None):
    """Add an image to an existing List, without modifying other images already supplied.
    Returns the image added and the modified list."""
    lst = models.List.objects.filter(slug=slug).first()
    if not lst:
        return None
    image = models.Image.objects.filter(identifier=image_identifier).first()
    if image:
        lst.images.add(image)
        lst.save()
    return image, lst

def delete_image_from_list(slug, image_identifier=None):
    """Add an image to an existing List, without modifying other images already supplied.
    Returns the image added and the modified list."""
    lst = models.List.objects.filter(slug=slug).first()
    if not lst:
        return None
    image = models.Image.objects.filter(identifier=image_identifier).first()
    if image:
        lst.images.remove(image)
        lst.save()
    return image, lst
