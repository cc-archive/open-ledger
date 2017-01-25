from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline
from imageledger import models
from django.contrib.admin.widgets import AdminFileWidget
from django.utils.translation import ugettext as _
from django.utils.safestring import mark_safe


class ImageAdmin(admin.ModelAdmin):
    fields = ( 'image_tag', 'title', 'provider', 'license', 'license_version')
    readonly_fields = ('image_tag',)

class ImageInline(admin.TabularInline):
    model = models.List.images.through

class ListAdmin(admin.ModelAdmin):
    inlines = [ ImageInline, ]
    exclude = ('images',)

admin.site.register(models.List, ListAdmin)
admin.site.register(models.Image, ImageAdmin)
