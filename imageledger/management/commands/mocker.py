import uuid
import random
import sys
import os
import io
import time
import itertools
import pdb
import traceback

sys.path.append("..")
from imageledger import models
from django.core.management.base import BaseCommand
from django.db import connection
from multiprocessing import Manager, Pool, Process

"""
A utility for inserting large amounts of random data into the database. This is tailored for stress testing full text
search in PostgreSQL.

Tip: drop indexes if you're inserting > 10M records. Recreate them after the job finishes.
"""


class TColors:
    WARNING = '\033[33m'
    RESET = '\033[0m'


class MockDataProducer(Process):
    """ Creates mock data and pushes the results to a message queue."""
    def __init__(self, num_results, result_queue, num_workers, num_worker_images, producer_finished):
        Process.__init__(self)
        self.done = False
        self.result_queue = result_queue
        self.num_workers = num_workers
        self.num_worker_images = num_worker_images
        self.num_results = num_results
        self.producer_finished = producer_finished
        english_words = set()
        with open(os.path.join(os.path.dirname(__file__), 'all_english_words.txt'), 'r') as english_dictionary:
            for line in english_dictionary:
                english_words.add(line.rstrip())

        self.com_words = random.sample(list(english_words), 50000)
        self.fake_creators = random.sample(list(english_words), 5000)
        self.queue_limit = 10

    def run(self):
        mock_count = 0
        print('Starting MockDataProducer')
        pool = Pool(self.num_workers)
        required_iterations = int(self.num_results / (self.num_worker_images * self.num_workers))
        for i in range(0, required_iterations):
            results = pool.starmap(
                generate_n_mock_images,
                [[self.num_worker_images, self.com_words, self.fake_creators] for _ in range(self.num_workers)]
            )
            # Flatten pool results into a single list and enqueue
            result_imgs = list(itertools.chain.from_iterable(results))
            csv_imgs = image_models_to_binary(result_imgs)
            while self.result_queue.qsize() >= self.queue_limit:
                # The queue is getting big, wait for the DB pusher to catch up
                time.sleep(1)
            self.result_queue.put((csv_imgs, len(result_imgs)))
        print('Done producing data after mocking', mock_count)
        self.producer_finished.value = 1


class DatabasePusher(Process):
    """ Consumes mock data from a message queue and pushes it to the database. """
    def __init__(self, mock_data_queue, num_images_to_push, producer_finished):
        Process.__init__(self)
        self.mock_data_queue = mock_data_queue
        self.num_images_to_push = num_images_to_push
        self.producer_finished = producer_finished

    def run(self):
        print('Starting DatabasePusher')
        to_commit = io.StringIO('')
        total_commits = 0
        while self.producer_finished.value == 0 or self.mock_data_queue.qsize() > 0:
            count = 0
            num_to_commit = 0
            while not self.mock_data_queue.empty() and count < 3:
                count += 1
                image_csv, num_images = self.mock_data_queue.get()
                to_commit = io.StringIO(to_commit.getvalue() + image_csv.getvalue())
                num_to_commit += num_images
            if to_commit.getvalue() != '':
                print('Pushing', num_to_commit, 'records to database')
                start_time = time.time()
                with connection.cursor() as cur:
                    cur.copy_from(to_commit,
                                   'image',
                                   columns=['title',
                                            'tags_list',
                                            'creator',
                                            'url',
                                            'thumbnail',
                                            'foreign_landing_url',
                                            'license',
                                            'provider',
                                            'source',
                                            'license_version',
                                            'creator_url',
                                            'filesize',
                                            'created_on',
                                            'updated_on',
                                            'removed_from_source'
                                            ]
                                  )
                connection.commit()
                commit_time = time.time() - start_time
                total_commits += num_to_commit
                print('Committed', num_to_commit, 'in', commit_time,
                      'seconds', '(' + str(num_to_commit / commit_time), 'per second)')
                print('Progress: ', total_commits / self.num_images_to_push * 100, '%', sep='')
                to_commit = io.StringIO('')
            time.sleep(1)
        print('Done pushing after committing', total_commits)


class Command(BaseCommand):
    can_import_settings = True
    requires_migrations_checks = True

    def add_arguments(self, parser):
        parser.add_argument('record_count', metavar='N', type=int, help='The number of mock records to generate.',
                            default=10000)
        parser.add_argument('--noninteractive', help='Run in non-interactive mode. Skips warning prompt.',
                            action='store_true')

    def handle(self, *args, **options):
        count = options['record_count']
        if count < 50000:
            print("Error: minimum of 50,000 mock records required")
            exit(1)

        if not options['noninteractive']:
            print(TColors.WARNING + 'Running this script will result in the following database receiving junk test'
                                    ' data:')
            print('Database', connection.settings_dict['NAME'], 'on host', connection.settings_dict['HOST'])
            print('Are you sure you want to continue?' + TColors.RESET)
            _continue = input('y/n\n').lower() == 'y'
            if not _continue:
                exit(0)

        print('Inserting random data\n')
        with Manager() as manager:
            producer_finished_signal = manager.Value('i', 0)
            mock_data_queue = manager.Queue()
            mock_data_producer = MockDataProducer(num_results=count,
                                                  result_queue=mock_data_queue,
                                                  num_workers=4,
                                                  num_worker_images=5000,
                                                  producer_finished=producer_finished_signal)
            db_pusher = DatabasePusher(mock_data_queue=mock_data_queue,
                                       num_images_to_push=count,
                                       producer_finished=producer_finished_signal)
            mock_data_producer.start()
            db_pusher.start()
            db_pusher.join()
            print('\nDone')


def make_mock_image(common_words, creators):
    """ Create a mock image generated from random data. Don't bother with any unsearchable fields. """
    image = {}

    num_words_in_title = random.randrange(1, 4)
    title = ""
    for idx, _ in enumerate(range(num_words_in_title)):
        title += random.sample(common_words, 1)[0] + ' '
    image['title'] = title

    num_tags = random.randrange(1, 4)
    tags_list = []
    for _ in range(num_tags):
        tags_list.append(random.choice(common_words))
    image['tags_list'] = str(tags_list).replace('[', '{').replace(']', '}')

    fake_url = 'www.example.com/'
    image['creator'] = random.choice(creators)
    image['url'] = fake_url + str(uuid.uuid4())
    image['thumbnail'] = fake_url + str(uuid.uuid4())
    image['foreign_landing_url'] = fake_url + str(uuid.uuid4())
    image['license'] = 'by'
    image['provider'] = 'flickr'
    image['source'] = 'openimages'
    image['license_version'] = '2.0'
    image['creator_url'] = str(fake_url + str(uuid.uuid4()))
    image['filesize'] = str(42)
    image['created_on'] = '1901-01-01 00:00:00.000000+00'
    image['updated_on'] = '1901-01-01 00:00:00.000000+00'
    image['removed_from_source'] = 'f'

    return image


def image_models_to_binary(images: list):
    """
    Given a list of Image models, convert the result to an in-memory CSV. This allows faster transfers to the database
    via COPY FROM.
    """
    csv_images = io.StringIO()
    for image in images:
        row = '\t'.join([image['title'],
                         image['tags_list'],
                         image['creator'],
                         image['url'],
                         image['thumbnail'],
                         image['foreign_landing_url'],
                         image['license'],
                         image['provider'],
                         image['source'],
                         image['license_version'],
                         image['creator_url'],
                         image['filesize'],
                         image['created_on'],
                         image['updated_on'],
                         image['removed_from_source']]) + '\n'

        csv_images.write(row)
    csv_images.seek(0)
    return csv_images


def generate_n_mock_images(n, common_words, creators):
    start_time = time.time()
    result = [make_mock_image(common_words, creators) for _ in range(n)]
    end_time = time.time()
    print('Worker generated', n / (end_time - start_time), 'records per second')
    return result
