import base64
import hashlib
import uuid

from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils.text import slugify

from imageledger import models

@receiver(pre_save, sender=models.Image)
def set_identifier(sender, instance, **kwargs):
    if instance.identifier is None:
        instance.identifier = create_identifier(instance.url)

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
