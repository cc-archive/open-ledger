from django.test import TestCase
from psycopg2.extensions import new_array_type

from imageledger import models, signals

class TestModels(TestCase):

    def test_db_connection(self):
        """The test database should be accessible"""
        assert models.Image.objects.count() == 0

    def test_image_model(self):
        """It should be possible to create an Image record with a few basic fields"""
        assert models.Image.objects.count() == 0
        image = models.Image()
        image.url = 'http://example.com'
        image.license = 'CC0'
        image.save()
        assert models.Image.objects.count() == 1

    def test_image_model_repr(self):
        """An image model representation should include its identifer, url, and creator"""
        url = "http://example.com"
        creator = "jane doe"
        image = models.Image(url=url, license="CC0", creator=creator)
        assert url in image.__repr__()
        assert creator in image.__repr__()


    def test_image_model_identifier(self):
        """The identifier-creation function should return the same value for each iteration"""
        url = 'http://example.com'
        last_identifier = None
        for i in range(0, 100):
            identifier = signals.create_identifier(url)
            if last_identifier:
                assert last_identifier == identifier
            else:
                last_identifier = identifier

    def test_tag_model(self):
        """It should be possible to create a Tag with a few basic fields"""
        assert models.Tag.objects.count() == 0
        tag = models.Tag()
        tag.name = 'myname'
        tag.foreign_identifier = '1234'
        tag.save()
        assert models.Tag.objects.count() == 1

    def test_tag_image(self):
        """It should be possible to associate a tag with an image"""
        image = models.Image(url='http://example.com', license="CC0")
        tag = models.Tag(name='tagname', foreign_identifier='tagid')
        tag.save()
        image.save()
        image_tag = models.ImageTags(image=image, tag=tag)
        image_tag.save()

    def test_tags_list_image(self):
        """The `tags_list` field on the `Image` table should contain an array of values"""
        image = models.Image(url='http://example.com', license="CC0")
        tags_list = ['a', 'b']
        image.tags_list = tags_list
        image.save()

        # Get it back out and assert that it's a list again
        image = models.Image.objects.all().first()
        assert 2 == len(image.tags_list)
        assert "a" == image.tags_list[0]

    def test_list(self):
        """It should be possible to create an empty List"""
        assert 0 == models.List.objects.count()
        lst = models.List(title='test')
        lst.save()

        assert 1 == models.List.objects.count()

    def test_list(self):
        """It should be possible to create a List and add an image to it"""

        image = models.Image(url='http://example.com', license="CC0")
        lst = models.List(title='test')
        lst.save()
        image.save()

        lst.images.add(image)

        assert 1 == models.List.objects.count()
        assert 1 == models.List.objects.first().images.count()
        assert image == models.List.objects.first().images.first()

    def test_slugify(self):
        """It should be possible to generate a URL-safe identifier out of an arbitrary list of keywords"""
        # A string, some crazy unicode, an integer
        items = ['my list', '☃', 1]
        assert 'my-list--1' == signals.create_slug(items)

    def test_slugify_list(self):
        """When a List is created, a slug should be automatically generated"""
        title = 'my list about unicode snowmen ☃'
        lst = models.List(title=title)
        lst.save()
        lst = models.List.objects.all().first()
        assert lst.slug.startswith('my-list-about-unicode-snowmen-')

    def test_slugify_unique(self):
        """Creating two lists with the same title should not result in a duplicate slug"""
        title = "Duplicate title"
        expected_slugged_title = "duplicate-title"
        lst1 = models.List(title=title)
        lst2 = models.List(title=title)
        lst1.save()
        lst2.save()

        lst1 = models.List.objects.all()[0]
        lst2 = models.List.objects.all()[1]
        # They should start the same, but not be identical
        assert lst1.slug.startswith(expected_slugged_title)
        assert lst2.slug.startswith(expected_slugged_title)
        assert lst1.slug != lst2.slug
