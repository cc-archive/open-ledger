from django.db.models.signals import pre_save

from django.apps import AppConfig

class ImageledgerConfig(AppConfig):
    name = 'imageledger'
    verbose_name = "Image Ledger"

    def ready(self):
        from imageledger.signals import set_identifier, create_slug
        from imageledger import search
        search.init()
