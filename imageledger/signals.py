import base64
import hashlib
import logging
import uuid

from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.utils.text import slugify
from django.conf import settings

from imageledger import models, search

log = logging.getLogger(__name__)

@receiver(pre_save, sender=models.Image)
def set_identifier(sender, instance, **kwargs):
    if instance.identifier is None:
        instance.identifier = create_identifier(instance.url)

@receiver(post_save, sender=models.Image)
def update_search_index(sender, instance, **kwargs):
    """When an Image instance is saved, tell the search engine about it."""
    if not settings.TESTING:
        _update_search_index(instance)

def _update_search_index(img):
    # FIXME This may result in a lot of concurrent requests during batch updates;
    # in those cases consider unregistering this signal and manually batching requests
    # (note that Django's bulk_create will not fire this signal, which is good)
    search_obj = search.db_image_to_index(img)
    if (search_obj.removed_from_source):
        log.debug("Removing image %s from search index", img.identifier)
        search_obj.delete()
    else:
        log.debug("Indexing image %s", img.identifier)
        search_obj.save()


def create_identifier(key):
    """Create a unique, stable identifier for a key"""
    m = hashlib.md5()
    m.update(bytes(key.encode('utf-8')))
    return base64.urlsafe_b64encode(m.digest()).decode('utf-8')

@receiver(pre_save, sender=models.List)
def set_slug(sender, instance, **kwargs):
    if instance.slug is None:
        uniquish = str(uuid.uuid4())[:8]
        instance.slug = create_slug([instance.title, uniquish])

def create_slug(el):
    """For the list of items el, create a unique slug out of them"""
    return '-'.join([slugify(str(i)) for i in el])
