# encoding: utf-8

LICENSES = (
    ("BY", "BY"),
    ("BY-NC", "BY-NC"),
    ("BY-ND", "BY-ND"),
    ("BY-SA", "BY-SA"),
    ("BY-NC-ND", "BY-NC-ND"),
    ("BY-NC-SA", "BY-NC-SA"),
    ("PDM", "PDM"),
    ("CC0", "CC0"),
)
LICENSE_GROUPS = {
    # All open licenses
    "ALL": ('BY', 'BY-NC', 'BY-ND', 'BY-SA', 'BY-NC-ND', 'BY-NC-SA', 'PDM', 'CC0'),
    # All CC licenses
    "ALL-CC": ('BY', 'BY-NC', 'BY-ND', 'BY-SA', 'BY-NC-ND', 'BY-NC-SA'),
    # All licenses allowing commercial use
    "ALL-$": ('BY', 'BY-SA', 'BY-ND', 'CC0', 'PDM'),
    # All licenses allowing modifications
    "ALL-MOD": ('BY', 'BY-SA', 'BY-NC', 'BY-NC-SA', 'CC0', 'PDM'),
}

def license_map_from_partners():
    """Returns a dictionary of each partner with known licensing schemes, and their
    mapping of license key to their internal identifier.

    This is used for display only: to go from a Flickr result containing
    `license_type=2` to a displayable value"""

    from openledger.handlers.handler_500px import LICENSE_LOOKUP as licenses_500px
    from openledger.handlers.handler_flickr import LICENSE_LOOKUP as licenses_flickr

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
    comma-separated list of values. Also handles special license group by
    expanding them into discrete licenses first. Licenses are always
    returned in ascending order.

    If an unknown license is passed in, it is ignored."""

    full_license_set = licenses[:]
    for license in licenses:
        if LICENSE_GROUPS.get(license):
            full_license_set += LICENSE_GROUPS.get(license)
    license_strings = sorted([str(license_dict.get(k)) for k in full_license_set if license_dict.get(k)])
    return ",".join(license_strings) if license_strings else None
