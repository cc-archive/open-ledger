from django.db import models
from django.contrib.postgres.fields import ArrayField

class OpenLedgerModel(models.Model):

    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)


    class Meta:
        abstract = True

class Image(OpenLedgerModel):

    # A unique identifier that we assign on ingestion. This is "our" identifier.
    # See the event handler below for the algorithm to generate this value
    identifier = models.CharField(unique=True, max_length=255, blank=True, null=True, db_index=True)

    # The perceptual hash we generate from the source image TODO
    perceptual_hash = models.CharField(unique=True, max_length=255, blank=True, null=True, db_index=True)

    # The provider of the data, typically a partner like Flickr or 500px
    provider = models.CharField(max_length=80, blank=True, null=True, db_index=True)

    # The source of the data, meaning a particular dataset. Source and provider
    # can be different: the Google Open Images dataset is source=openimages,
    # but provider=Flickr (since all images are Flickr-originated)
    source = models.CharField(max_length=80, blank=True, null=True, db_index=True)

    # The identifier that was defined by the source or provider. This may need
    # to be extended to support multiple values when we begin to reconcile duplicates
    foreign_identifier = models.CharField(unique=True, max_length=80, blank=True, null=True, db_index=True)

    # The entry point URL that we got from the external source, such as the
    # HTTP referrer, or the landing page recorded by the provider/source
    foreign_landing_url = models.CharField(max_length=1000, blank=True, null=True)

    # The actual URL to the primary resolution of the image
    # Note that this is unique!
    url = models.URLField(unique=True, max_length=1000)

    # The primary thumbnail URL for this image
    thumbnail = models.URLField(max_length=1000, blank=True, null=True)

    # Image dimensions, if available
    width = models.IntegerField(blank=True, null=True)
    height = models.IntegerField(blank=True, null=True)

    # The original filesize, if available, in bytes
    filesize = models.IntegerField(blank=True, null=True)

    # The license string as specified in licenses.py
    # This field is _required_, we have no business having a record of an image
    # if we don't know its license
    license = models.CharField(max_length=50)

    # The license version as a string, optional as we may not have good metadata
    # This is a string to accommodate potential oddball/foreign values, but normally
    # should be a decimal like "2.0"
    license_version = models.CharField(max_length=25, blank=True, null=True)

    # The author/creator/licensee, not that we'll know for sure
    creator = models.CharField(max_length=2000, blank=True, null=True)

    # The URL to the creator's identity or profile, if known
    creator_url = models.URLField(max_length=2000, blank=True, null=True)

    # The title of the image, if available
    title = models.CharField(max_length=2000, blank=True, null=True)

    # Denormalized tags as an array, for easier syncing with Elasticsearch
    tags_list = ArrayField(models.CharField(max_length=255), blank=True, null=True)

    def __str__(self):
        return '<Image %r found at %r by %r>' % (self.identifier, self.url, self.creator)

    class Meta:
        db_table = 'image'


class ImageTags(OpenLedgerModel):
    tag = models.ForeignKey('Tag', on_delete=models.CASCADE, blank=True, null=True)
    image = models.ForeignKey(Image, on_delete=models.CASCADE, blank=True, null=True)

    class Meta:
        db_table = 'image_tags'

class List(OpenLedgerModel):
    title = models.CharField(max_length=2000)
    creator_displayname = models.CharField(max_length=2000, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    is_public = models.NullBooleanField()
    slug = models.CharField(unique=True, max_length=255, blank=True, null=True)
    images = models.ManyToManyField(Image)
    class Meta:
        db_table = 'list'


class Tag(OpenLedgerModel):
    foreign_identifier = models.CharField(max_length=255, blank=True, null=True)
    name = models.CharField(max_length=1000, blank=True, null=True)
    source = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = 'tag'
