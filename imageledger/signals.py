import base64
import hashlib
import logging
import uuid

from django.db.models.signals import pre_save, post_save, post_delete
from django.contrib.auth import get_user_model
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
        search_obj.delete(ignore=404)
    else:
        log.debug("Indexing image %s", img.identifier)
        search_obj.save()

def create_identifier(key):
    """Create a unique, stable identifier for a key"""
    m = hashlib.md5()
    m.update(bytes(key.encode('utf-8')))
    return base64.urlsafe_b64encode(m.digest()).decode('utf-8')

@receiver(pre_save, sender=models.Tag)
@receiver(pre_save, sender=models.List)
def set_slug(sender, instance, **kwargs):
    if instance.slug is None:
        uniquish = str(uuid.uuid4())[:8]
        title_field = instance.title if hasattr(instance, 'title') else instance.name
        slug = create_slug([title_field, uniquish])
        instance.slug = slug

def create_slug(el):
    """For the list of items el, create a unique slug out of them"""
    return '-'.join([slugify(str(i)) for i in el])

@receiver(post_save, sender=models.Favorite)
def add_to_favorite_list(sender, instance, created, **kwargs):
    """Add to the Favorites list when a Favorite is added"""
    if created:
        lst, created = models.List.objects.get_or_create(title=models.List.FAVORITE_LABEL, owner=instance.user)
        lst.images.add(instance.image)

@receiver(post_delete, sender=models.Favorite)
def remove_from_favorite_list(sender, instance, **kwargs):
    """Remove from the Favorites list when a Favorite is removed"""
    lst = models.List.objects.filter(title=models.List.FAVORITE_LABEL, owner=instance.user).first()
    if lst:
        lst.images.remove(instance.image)

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_favorites_list(sender, instance, created, **kwargs):
    if created:
        models.List.objects.create(title=models.List.FAVORITE_LABEL, owner=instance)
