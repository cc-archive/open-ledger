import itertools
import logging
import time

from django.db.utils import IntegrityError
import elasticsearch
import requests

from imageledger import models, signals, search

log = logging.getLogger(__name__)

def grouper_it(n, iterable):
    it = iter(iterable)
    while True:
        chunk_it = itertools.islice(it, n)
        try:
            first_el = next(chunk_it)
        except StopIteration:
            return
        yield itertools.chain((first_el,), chunk_it)

def insert_image(walk_func, serialize_func, chunk_size, max_results=5000):
    count = 0
    success_count = 0
    es = search.init()
    search.Image.init()
    mapping = search.Image._doc_type.mapping
    mapping.save('openledger')

    for chunk in grouper_it(chunk_size, walk_func()):
        if count >= max_results:
            break
        else:
            images = []
            for result in chunk:
                image = serialize_func(result)
                images.append(image) if image
            if len(images) > 0:
                try:
                    # Bulk update the search engine too
                    es.cluster.health(wait_for_status='green', request_timeout=2000)
                    search_objs = [search.db_image_to_index(img).to_dict(include_meta=True) for img in images]
                    elasticsearch.helpers.bulk(es, search_objs)
                    models.Image.objects.bulk_create(images)
                    log.debug("*** Committed set of %d images", len(images))
                    success_count += len(images)
                except (requests.exceptions.ReadTimeout,
                        elasticsearch.exceptions.TransportError,
                        elasticsearch.helpers.BulkIndexError,
                        IntegrityError) as e:
                    log.warn("Got one or more integrity errors on batch: %s", e)
                finally:
                    count += len(images)
    return success_count
