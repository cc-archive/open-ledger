# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey has `on_delete` set to the desired behavior.
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from __future__ import unicode_literals

from django.db import models


class Image(models.Model):

    identifier = models.CharField(unique=True, max_length=255, blank=True, null=True)
    perceptual_hash = models.CharField(unique=True, max_length=255, blank=True, null=True)
    provider = models.CharField(max_length=80, blank=True, null=True)
    source = models.CharField(max_length=80, blank=True, null=True)
    foreign_identifier = models.CharField(unique=True, max_length=80, blank=True, null=True)
    foreign_landing_url = models.CharField(max_length=1000, blank=True, null=True)
    url = models.CharField(unique=True, max_length=1000)
    width = models.IntegerField(blank=True, null=True)
    height = models.IntegerField(blank=True, null=True)
    filesize = models.IntegerField(blank=True, null=True)
    license = models.CharField(max_length=50)
    license_version = models.CharField(max_length=25, blank=True, null=True)
    creator = models.CharField(max_length=2000, blank=True, null=True)
    creator_url = models.CharField(max_length=2000, blank=True, null=True)
    title = models.CharField(max_length=2000, blank=True, null=True)
    tags_list = models.TextField(blank=True, null=True)  # This field type is a guess.
    created_on = models.DateTimeField(blank=True, null=True)
    updated_on = models.DateTimeField(blank=True, null=True)
    thumbnail = models.CharField(max_length=1000, blank=True, null=True)

    class Meta:
        db_table = 'image'


class ImageTags(models.Model):
    tag = models.ForeignKey('Tag', on_delete=models.CASCADE, blank=True, null=True)
    image = models.ForeignKey(Image, on_delete=models.CASCADE, blank=True, null=True)
    created_on = models.DateTimeField(blank=True, null=True)
    updated_on = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'image_tags'


class List(models.Model):
    title = models.CharField(max_length=2000)
    creator_displayname = models.CharField(max_length=2000, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    is_public = models.NullBooleanField()
    slug = models.CharField(unique=True, max_length=255, blank=True, null=True)
    created_on = models.DateTimeField(blank=True, null=True)
    updated_on = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'list'


class ListImages(models.Model):
    list = models.ForeignKey(List, on_delete=models.CASCADE, blank=True, null=True)
    image = models.ForeignKey(Image, on_delete=models.CASCADE, blank=True, null=True)
    created_on = models.DateTimeField(blank=True, null=True)
    updated_on = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'list_images'
        unique_together = (('list', 'image'),)


class Tag(models.Model):
    foreign_identifier = models.CharField(max_length=255, blank=True, null=True)
    name = models.CharField(max_length=1000, blank=True, null=True)
    source = models.CharField(max_length=255, blank=True, null=True)
    created_on = models.DateTimeField(blank=True, null=True)
    updated_on = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'tag'
