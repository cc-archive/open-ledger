# encoding: utf-8
import logging
from urllib.parse import urlparse

log = logging.getLogger(__name__)

LICENSE_URL_BASE = "https://creativecommons.org"

LICENSES = (
    ("BY", "Attribution"),
    ("BY-NC", "Attribution NonCommercial"),
    ("BY-ND", "Attribution NoDerivatives"),
    ("BY-SA", "Attribution ShareAlike"),
    ("BY-NC-ND", "Attribution NonCommercial NoDerivatives"),
    ("BY-NC-SA", "Attribution NonCommercial ShareAlike"),
    ("PDM", "Public Domain Mark"),
    ("CC0", "Public Domain Dedication"),
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

LICENSE_LIST = set(l[0] for l in LICENSES)

DEFAULT_LICENSE = "ALL"

LICENSE_LIST.update(set(l for l in LICENSE_GROUPS.keys()))

class LicenseException(Exception):
    pass

def get_license_url(license, version):
    """For a given version and license string, return the canonical human-readable deed"""
    if not license:
        raise LicenseException("No license was provided")
    if not version:
        raise LicenseException("No version was provided")

    if not license.upper() in set(l[0] for l in LICENSES):
        log.warn("Unknown license was provided: %r", license)
        return None

    license = license.lower()

    if license == 'cc0':
        # Always version 1.0?
        return "{}/publicdomain/zero/1.0".format(LICENSE_URL_BASE)
    elif license == 'pdm':
        # Always version 1.0?
        return "{}/publicdomain/mark/1.0".format(LICENSE_URL_BASE)
    elif license and version:
        return "{}/licenses/{}/{}".format(LICENSE_URL_BASE, license, version)

def url_to_license(url):
    """Given a URL, return the license"""
    (scheme, netloc, path, *remainder) = urlparse(url)
    path_parts = path.split('/')
    if len(path_parts) != 4:
        raise LicenseException("Did not get 4 path segments, probably not a CC license URL")
    license = path_parts[2].upper()  # First is '', because it starts with a leading /
    version = path_parts[3]

    # Handle the PD licenses as special-cases
    if license == 'ZERO':
        license = 'CC0'
        version = None
    if license == 'MARK':
        license = 'PDM'
        version = None
    if license not in LICENSE_LIST:
        raise LicenseException("License fragment %s was not a valid license", license)
    if version:
        return "{} {}".format(license, version)
    else:
        return license

def license_map_from_partners():
    """Returns a dictionary of each partner with known licensing schemes, and their
    mapping of license key to their internal identifier.

    This is used for display only: to go from a Flickr result containing
    `license_type=2` to a displayable value"""

    from imageledger.handlers.handler_500px import LICENSE_LOOKUP as licenses_500px, LICENSE_VERSION as version_500px
    from imageledger.handlers.handler_flickr import LICENSE_LOOKUP as licenses_flickr, LICENSE_VERSION as version_flickr
    from imageledger.handlers.handler_rijks import LICENSE_VERSION as version_rijks
    from imageledger.handlers.handler_wikimedia import LICENSE_VERSION as version_wikimedia

    l500px = {}
    l500px.update(licenses_500px)
    l500px['version'] = version_500px

    lflickr = {}
    lflickr.update(licenses_flickr)
    lflickr['version'] = version_flickr

    return {
        "fpx": l500px,
        "flickr": lflickr,
        "wikimedia": {'version': version_wikimedia, 0: "CC0"},
        "rijks": {'version': version_rijks, 0: "CC0"}
    }

def license_match(licenses, license_dict):
    """Given an array of licenses chosen by a user and a dictionary of handler-
    specific license values, find all matching items and return a
    comma-separated list of values. Also handles special license group by
    expanding them into discrete licenses first. Licenses are always
    returned in ascending order.

    If an unknown license is passed in, it is ignored."""

    full_license_set = licenses[:]
    license_groups_selected = []
    for license in licenses:
        if LICENSE_GROUPS.get(license):
            license_groups_selected.append([x for x in LICENSE_GROUPS.get(license)])

    # If we got some license groups, filter down to the intersection of those
    if license_groups_selected:
        full_license_set = set.intersection(*map(set, license_groups_selected))
    license_strings = sorted([str(license_dict.get(k)) for k in full_license_set if license_dict.get(k)])
    return ",".join(license_strings) if license_strings else None
