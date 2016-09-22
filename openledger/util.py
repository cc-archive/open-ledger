# encoding: utf-8
from openledger.handlers.handler_500px import LICENSE_LOOKUP as licenses_500px
from openledger.handlers.handler_flickr import LICENSE_LOOKUP as licenses_flickr

def licenses():
    """Returns a dictionary to allow lookup by any known scheme"""
    l500px = {}
    l500px.update(licenses_500px)
    lflickr = {}
    lflickr.update(licenses_flickr)

    return {
        "fpx": l500px,
        "flickr": lflickr
    }
