from django.test import TestCase

from imageledger import licenses
from imageledger.handlers import handler_500px, handler_flickr

from imageledger import models, signals

class TestModels(TestCase):

    def test_license_match_simple(self):
        """The license_match() function should match an array of license names
        to a comma-separated string of values from a partner mapping"""
        mapping = handler_500px.LICENSES
        assert '4' == licenses.license_match(["BY"], mapping)
        assert '1,4' == licenses.license_match(["BY", "BY-NC"], mapping)

        mapping = handler_flickr.LICENSES
        assert '4' == licenses.license_match(["BY"], mapping)
        assert '2,7' == licenses.license_match(["BY-NC", "PDM"], mapping)

    def test_license_match_unknown_license(self):
        """The license match function should ignore unknown licenses"""
        mapping = handler_flickr.LICENSES
        assert None == licenses.license_match(["UNKNOWN"], mapping)

    def test_license_match_partial_unknown_license(self):
        """The license match function should ignore unknown licenses
        but still include known ones"""
        mapping = handler_flickr.LICENSES
        assert '4' == licenses.license_match(["UNKNOWN", "BY"], mapping)

    def test_license_match_groups(self):
        """The license match function should expand out logical groups of licenses"""
        mapping = handler_flickr.LICENSES
        assert '1,2,3,4,5,6,7,9' == licenses.license_match(["ALL"], mapping)
        assert '1,2,3,4,5,6' == licenses.license_match(["ALL-CC"], mapping)
        assert '4,5,6,7,9' == licenses.license_match(["ALL-$"], mapping)
        assert '1,2,4,5,7,9' == licenses.license_match(["ALL-MOD"], mapping)

    def test_license_match_groups_intersection(self):
        """The license match function should return the intersection of multiple groups, not the union"""
        mapping = handler_flickr.LICENSES
        assert '4,5,7,9' == licenses.license_match(["ALL-$", "ALL-MOD"], mapping)

    def test_license_map_version(self):
        """The license match function should return a special `version` key that includes
        the correct static license version associated with each provider"""
        license_map = licenses.license_map_from_partners()
        assert "1.0" == license_map['rijks']['version']
        assert "1.0" == license_map['wikimedia']['version']
        assert "3.0" == license_map['fpx']['version']
        assert "2.0" == license_map['flickr']['version']

    def test_license_map_lookup(self):
        """The license map function should return a known key for a license value by provider"""
        license_map = licenses.license_map_from_partners()
        assert "CC0" == license_map['fpx'][8]
        assert "CC0" == license_map['flickr'][9]

    def test_license_map_pd_sources(self):
        """The license map function should return a value of CC0 for a default lookup of 0"""
        license_map = licenses.license_map_from_partners()
        assert "CC0" == license_map['wikimedia'][0]
        assert "CC0" == license_map['rijks'][0]

    def test_get_license_url_license(self):
        """The license URL method should return the expected URL for a license type"""
        assert "https://creativecommons.org/licenses/by/4.0" == licenses.get_license_url("by", "4.0")
        assert "https://creativecommons.org/licenses/by-sa/4.0" == licenses.get_license_url("by-sa", "4.0")
        assert "https://creativecommons.org/licenses/by-nc/4.0" == licenses.get_license_url("by-nc", "4.0")
        assert "https://creativecommons.org/licenses/by-nc-nd/4.0" == licenses.get_license_url("by-nc-nd", "4.0")
        assert "https://creativecommons.org/licenses/by-nc-sa/4.0" == licenses.get_license_url("by-nc-sa", "4.0")

    def test_get_license_url_version(self):
        """The license URL method should return the expected URL for a license version"""
        assert "https://creativecommons.org/licenses/by/3.0" == licenses.get_license_url("by", "3.0")
        assert "https://creativecommons.org/licenses/by-sa/3.0" == licenses.get_license_url("by-sa", "3.0")
        assert "https://creativecommons.org/licenses/by-nc/3.0" == licenses.get_license_url("by-nc", "3.0")
        assert "https://creativecommons.org/licenses/by-nc-nd/3.0" == licenses.get_license_url("by-nc-nd", "3.0")
        assert "https://creativecommons.org/licenses/by-nc-sa/3.0" == licenses.get_license_url("by-nc-sa", "3.0")

    def test_get_license_url_no_version(self):
        """The license URL method should return an exception if not passed a version"""
        self.assertRaises(licenses.LicenseException, licenses.get_license_url, "by", None)

    def test_get_license_url_no_license(self):
        """The license URL method should return an exception if not passed a license"""
        self.assertRaises(licenses.LicenseException, licenses.get_license_url, None, "3.0")

    def test_get_license_url_unknown_license(self):
        """The license URL method should return None if passed an unknown license"""
        assert licenses.get_license_url("FAKE", "3.0") is None

    def test_get_license_url_pd_licenses(self):
        """The license URL method should return the correct public domain licenses regardless of version"""
        assert "https://creativecommons.org/publicdomain/zero/1.0" == licenses.get_license_url("cc0", "10.0")
        assert "https://creativecommons.org/publicdomain/mark/1.0" == licenses.get_license_url("pdm", "10.0")

    def test_url_to_license(self):
        """The URL-to-license method should return the correct license and version number given a well-formed URL"""
        url = "https://creativecommons.org/licenses/by/3.0"
        self.assertEquals("BY 3.0", licenses.url_to_license(url))
        url = "https://creativecommons.org/licenses/by-nc/4.0"
        self.assertEquals("BY-NC 4.0", licenses.url_to_license(url))

    def test_url_to_pd_licenses(self):
        """The URL-to-license method should return the correct license and version number given a
        well-formed URL to the public domain licenses"""
        url = "https://creativecommons.org/publicdomain/zero/1.0"
        self.assertEquals("CC0", licenses.url_to_license(url))
        url = "https://creativecommons.org/publicdomain/mark/1.0"
        self.assertEquals("PDM", licenses.url_to_license(url))

    def test_url_to_license_unknown_license(self):
        """The URL to license method should raise an exception if an unknown URL is passed"""
        bad = "http://example.com"
        # Exceptions for both malformed URL and non-licenses
        self.assertRaises(licenses.LicenseException, licenses.url_to_license, bad)
        bad = "https://creativecommons.org/licenses/madeup/3.0"
        self.assertRaises(licenses.LicenseException, licenses.url_to_license, bad)
