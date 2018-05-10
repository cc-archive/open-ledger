import uuid
import random
import sys
import os
import time
import pdb
import itertools

sys.path.append("..")
from imageledger import models
from django.core.management.base import BaseCommand
from django.db import connection
from multiprocessing import Pool

"""
A utility for inserting large amounts of random data into the database. This is tailored for stress testing full text
search in PostgreSQL.
"""


class Command(BaseCommand):
    can_import_settings = True
    requires_migrations_checks = True

    def add_arguments(self, parser):
        parser.add_argument('record_count', metavar='N', type=int, help='The number of mock records to generate.',
                            default=10000)
        parser.add_argument('--noninteractive', help='Run in non-interactive mode. Skips warning prompt.',
                            action='store_true')

    def handle(self, *args, **options):
        if not options['noninteractive']:
            print('Running this script will result in the following database receiving junk test data:')
            print('Database', connection.settings_dict['NAME'], 'on host', connection.settings_dict['HOST'])
            print('Are you sure you want to continue?')
            _continue = input('y/n\n').lower() == 'y'
            if not _continue:
                exit(0)

        english_words = set()
        print('Caching the English language. . .')
        with open(os.path.join(os.path.dirname(__file__), 'all_english_words.txt'), 'r') as english_dictionary:
            for line in english_dictionary:
                english_words.add(line.rstrip())
        print('Done caching.')
        com_words = random.sample(list(english_words), 50000)
        fake_creators = random.sample(list(english_words), 5000)
        print('Inserting random data\n')
        count = options['record_count']

        num_workers = 8
        worker_images = 5000
        # Number of images to generate before committing results
        chunk_size = max(10000, num_workers * worker_images)
        images = []
        pool = Pool(num_workers)

        required_iterations = int(count / (worker_images * num_workers))
        for i in range(0, required_iterations):
            results = pool.starmap(
                generate_n_mock_images,
                [[worker_images, com_words, fake_creators] for _ in range(num_workers)]
            )
            # Flatten pool results before storing
            images.extend(list(itertools.chain.from_iterable(results)))
            progress = round(i / required_iterations * 100, 3)
            if len(images) >= chunk_size or i == required_iterations - 1:
                # Commit to database after accumulating enough data
                print('Committing ', len(images), ' images. Total progress: ', progress, '%', sep='')
                commit_start_time = time.time()
                models.Image.objects.bulk_create(images)
                commit_time = time.time() - commit_start_time
                print('Committed', len(images), 'in', commit_time, 'seconds', '(' + str(len(images)/commit_time),
                      'per second)')
                images = []

        print('\nDone')


def make_mock_image(common_words, creators):
    """ Create a mock model.Image generated from random data. Don't bother with any unsearchable fields. """
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

    fake_url = 'www.example.com/'
    image.creator = random.choice(creators)
    image.url = fake_url + str(uuid.uuid4())
    image.thumbnail = fake_url + str(uuid.uuid4())
    image.foreign_landing_url = fake_url + str(uuid.uuid4())
    image.license = 'by'
    image.provider = 'flickr'
    image.source = 'openimages'
    image.license_version = '2.0'
    image.creator_url = fake_url + str(uuid.uuid4())
    image.filesize = 42

    return image


def generate_n_mock_images(n, common_words, creators):
    start_time = time.time()
    result = [make_mock_image(common_words, creators) for _ in range(n)]
    end_time = time.time()
    print('Worker generated', n / (end_time - start_time), 'records per second')
    return result
