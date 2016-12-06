def grouper_it(n, iterable):
    it = iter(iterable)
    while True:
        chunk_it = itertools.islice(it, n)
        try:
            first_el = next(chunk_it)
        except StopIteration:
            return
        yield itertools.chain((first_el,), chunk_it)

def insert_image(chunk_size, max_results=5000):
    count = 0
    success_count = 0
    es = search.init()
    search.Image.init()
    mapping = search.Image._doc_type.mapping
    mapping.save('openledger')

    for chunk in grouper_it(chunk_size, walk()):
        if count >= max_results:
            break
        else:
            images = []
            for result in chunk:
                image = serialize(result)
                images.append(image)
            if len(images) > 0:
                try:
                    # Bulk update the search engine too
                    search_objs = [search.db_image_to_index(img).to_dict(include_meta=True) for img in images]
                    helpers.bulk(es, search_objs)
                    models.Image.objects.bulk_create(images)
                    log.debug("*** Committed set of %d images", len(images))
                    success_count += len(images)
                except IntegrityError as e:
                    log.warn("Got one or more integrity errors on batch: %s", e)
                finally:
                    count += len(images)
    return success_count
