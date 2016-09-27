from openledger import licenses
from openledger.handlers import handler_500px, handler_flickr

def test_license_match_simple():
    """The license_match() function should match an array of license names
    to a comma-separated string of values from a partner mapping"""
    mapping = handler_500px.LICENSES
    assert '4' == licenses.license_match(["BY"], mapping)
    assert '1,4' == licenses.license_match(["BY", "BY-NC"], mapping)

    mapping = handler_flickr.LICENSES
    assert '4' == licenses.license_match(["BY"], mapping)
    assert '2,7' == licenses.license_match(["BY-NC", "PDM"], mapping)

def test_license_match_unknown_license():
    """The license match function should ignore unknown licenses"""
    mapping = handler_flickr.LICENSES
    assert None == licenses.license_match(["UNKNOWN"], mapping)

def test_license_match_partial_unknown_license():
    """The license match function should ignore unknown licenses
    but still include known ones"""
    mapping = handler_flickr.LICENSES
    assert '4' == licenses.license_match(["UNKNOWN", "BY"], mapping)

def test_license_match_groups():
    """The license match function should expand out logical groups of licenses"""
    mapping = handler_flickr.LICENSES
    assert '1,2,3,4,5,6,7,9' == licenses.license_match(["ALL"], mapping)
    assert '1,2,3,4,5,6' == licenses.license_match(["ALL-CC"], mapping)
    assert '4,5,6,7,9' == licenses.license_match(["ALL-$"], mapping)
    assert '1,2,4,5,7,9' == licenses.license_match(["ALL-MOD"], mapping)
