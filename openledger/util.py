# encoding: utf-8


def licenses():
    """Returns a dictionary to allow lookup by any known scheme"""
    from handlers.handler_500px import LICENSE_LOOKUP as licenses_500px
    from handlers.handler_flickr import LICENSE_LOOKUP as licenses_flickr
    
    # Allow both integers and strings
    licenses_500px.update({v: str(k) for k, v in licenses_500px.items()})
    licenses_flickr.update({v: str(k) for k, v in licenses_flickr.items()})
    return {
        "fpx": licenses_500px,
        "flickr": licenses_flickr
    }
