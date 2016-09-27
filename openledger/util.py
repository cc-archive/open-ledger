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

def license_match(licenses, license_dict):
    """Given an array of licenses chosen by a user and a dictionary of handler-
    specific license values, find all matching items and return a
    comma-separated list of values"""
    return ",".join([str(license_dict[k]) for k in licenses])
