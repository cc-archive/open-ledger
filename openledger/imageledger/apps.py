from django.db.models.signals import pre_save

from django.apps import AppConfig

class ImageledgerConfig(AppConfig):
    name = 'imageledger'
    verbose_name = "Image Ledger"

    def ready(self):
        import imageledger.signals
