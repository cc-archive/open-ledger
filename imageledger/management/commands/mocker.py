import getpass
import random
import sys
import os
import pdb

sys.path.append("..")
from imageledger import models
from django.core.management.base import BaseCommand

"""
A utility for inserting random data into the database. This is tailored for stress testing full text search in 
PostgreSQL.
"""


class Command(BaseCommand):
    can_import_settings = True
    requires_migrations_checks = True

    def add_arguments(self, parser):
        parser.add_argument('record_count', metavar='N', type=int,
                            help='The number of mock records to generate.',
                            default=10000)
        parser.add_argument('db_url', metavar='h', type=str, help='The database destination.')
        parser.add_argument('port', metavar='p', type=int, help='The destination port.', default=5432)
        parser.add_argument('user', metavar='U', type=str, help='The database user.', default='deploy')
        parser.add_argument('verbose', metavar='verbose', type=bool, help='Print additional diagnostic logs',
                            default=True)

    def handle(selfself, *args, **options):
        english_words = set()
        print('Caching the English language. . .')
        with open(os.path.join(os.path.dirname(__file__), 'all_english_words.txt'), 'r') as english_dictionary:
            for line in english_dictionary:
                english_words.add(line.rstrip())
        print('Done caching.')
        com_words = random.sample(list(english_words), 12000)
        fake_creators = random.sample(list(english_words), 5000)
        print('Inserting random data\n')
        count = options['record_count']
        chunk_size = 10000

        images = []
        for i in range(0, count):
            images.append(make_mock_image(english_words, com_words, fake_creators, i))
            progress = round(i / count * 100, 3)
            if len(images) == chunk_size or i == count - 1:
                models.Image.objects.bulk_create(images)

            if i % 5 == 0:
                # Print a status update every so often
                print('\r{:.2f}'.format(progress), '%', sep='', end="")
        print('')
        print('Done')


def make_mock_image(dictionary, common_words, creators, curr_count):
    """ Create a mock model.Image generated from random data. Don't bother with any unsearchable fields. """
    curr_count = str(curr_count)
    image = models.Image()

    num_words_in_title = random.randrange(1, 4)
    title = ""
    for idx, _ in enumerate(range(num_words_in_title)):
        title += random.sample(common_words, 1)[0] + ' '
    image.title = title

    num_tags = random.randrange(1, 4)
    tags_list = []
    for _ in range(num_tags):
        tags_list.append(random.choice(common_words))
    image.tags_list = tags_list

    image.creator = random.choice(creators)
    image.url = curr_count
    image.thumbnail = curr_count
    image.foreign_landing_url = curr_count
    image.license = 'by'
    image.provider = 'flickr'
    image.source = 'openimages'
    image.license_version = '2.0'
    image.creator_url = curr_count
    image.filesize = 42

    return image


