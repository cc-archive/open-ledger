import os

import pytest

from hashers import *

IMAGE_DIR = 'samples'

# A set of pairs of images that all begin with the same string, indicating what
# has changed between them
ALL_IMAGES = {}

IMAGE_TESTS = ('cropped',  # One image is a cropped version of the other
               'providers',  # Same work, same dimensions, but sourced from
                             # two different providers (different binaries)
               'color',      # Same image, desaturated and not
               'similar',    # Different images, but seen as "similar" by Google img query
               'memed',      # Same image, but with meme-like text applied
               )

THRESHOLD_IDENTITY = 12  # We'd like all values we consider to be identical to be
                           # at or below this value

THRESHOLD_SIMILARITY = 20 # We'd consider values below this (but above IDENTITY) to be likely derivative works


for test in IMAGE_TESTS:
    pair = [os.path.join(IMAGE_DIR, f) for f in os.listdir(IMAGE_DIR) if f.startswith(test)]
    ALL_IMAGES[test] = pair

def test_random():
    """Images with the random hasher should _(almost) always_ fail to return the same hash"""
    for imgset in ALL_IMAGES.values():
        assert random(imgset[0]) != random(imgset[1])

def test_different_threshold():
    """Totally different identifiers should exceed our THRESHOLD_IDENTITY"""
    h1 = 'e60439a9-49d5-4580-a024-eecc43fd4dd2'
    h2 = '418fafd3-37d8-477e-9b3e-11b60b060dd6'
    assert hamming_distance(h1, h2) > THRESHOLD_IDENTITY

def test_same_threshold():
    """Totally identical identifiers should have a difference value of 0"""
    h1 = 'e60439a9-49d5-4580-a024-eecc43fd4dd2'
    h2 = 'e60439a9-49d5-4580-a024-eecc43fd4dd2'
    assert 0 == hamming_distance(h1, h2)

def test_blockhash_same():
    """Processing the same image with the blockhash hasher twice should return the same hash"""
    imagefile = ALL_IMAGES['cropped'][0]
    hash1 = blockhash(imagefile)
    hash2 = blockhash(imagefile)
    assert hash1 == hash2

def test_blockhash_different():
    """Processing completely different images with the blockhash hasher twice should
    return different hashes"""
    imagefile1 = ALL_IMAGES['cropped'][0]
    imagefile2 = ALL_IMAGES['providers'][-1]
    hash1 = blockhash(imagefile1)
    hash2 = blockhash(imagefile2)
    assert hash1 != hash2

@pytest.mark.xfail
def test_blockhash_pairs_cropped():
    """Processing cropped pairs through the blockhash hasher should return "same" results
    Note: This is expected to fail; this algorithm doesn't come within the similarity guidelines
    for these images
    """
    imgs = ALL_IMAGES['cropped']
    h1 = blockhash(imgs[0])[imgs[0]]
    h2 = blockhash(imgs[1])[imgs[1]]
    dist = hamming_distance(h1, h2)
    assert dist <= THRESHOLD_IDENTITY

def test_blockhash_pairs_providers():
    """Processing providers pairs through the blockhash hasher should return "same" results"""
    imgs = ALL_IMAGES['providers']
    h1 = blockhash(imgs[0])[imgs[0]]
    h2 = blockhash(imgs[1])[imgs[1]]
    dist = hamming_distance(h1, h2)
    assert dist <= THRESHOLD_IDENTITY

def test_blockhash_pairs_color():
    """Processing color pairs through the blockhash hasher should return "same" results"""
    imgs = ALL_IMAGES['color']
    h1 = blockhash(imgs[0])[imgs[0]]
    h2 = blockhash(imgs[1])[imgs[1]]
    dist = hamming_distance(h1, h2)
    assert dist <= THRESHOLD_IDENTITY

def test_imagehash_same():
    """Processing the same image with the imagehash hasher twice should return the same hash"""
    imagefile = ALL_IMAGES['cropped'][0]
    hash1 = imagehash(imagefile)
    hash2 = imagehash(imagefile)
    assert hash1 == hash2

def test_imagehash_pairs_cropped():
    """Processing cropped pairs through the imagehash hasher should return "same" results
    Note: This is expected to fail; this algorithm doesn't come within the similarity guidelines
    for these images
    """
    imgs = ALL_IMAGES['cropped']
    h1 = imagehash(imgs[0])[imgs[0]]
    h2 = imagehash(imgs[1])[imgs[1]]
    dist = h1 - h2
    assert dist <= THRESHOLD_IDENTITY

def test_imagehash_pairs_providers():
    """Processing providers pairs through the imagehash hasher should return "same" results"""
    imgs = ALL_IMAGES['providers']
    h1 = imagehash(imgs[0])[imgs[0]]
    h2 = imagehash(imgs[1])[imgs[1]]
    dist = h1 - h2
    assert dist <= THRESHOLD_IDENTITY

def test_imagehash_pairs_color():
    """Processing color pairs through the imagehash hasher should return "same" results"""
    imgs = ALL_IMAGES['color']
    h1 = imagehash(imgs[0])[imgs[0]]
    h2 = imagehash(imgs[1])[imgs[1]]
    dist = h1 - h2
    assert dist <= THRESHOLD_IDENTITY

def test_imagehash_pairs_similar():
    """Processing two different images that were identified as "similiar" by Google image query
    should fall _above_ THRESHOLD_IDENTITY"""
    imgs = ALL_IMAGES['similar']
    h1 = imagehash(imgs[0])[imgs[0]]
    h2 = imagehash(imgs[1])[imgs[1]]
    dist = h1 - h2
    assert dist > THRESHOLD_IDENTITY   # Seems to return 28

def test_imagehash_pairs_memed():
    """The same image with overlaid text (like a meme) should be considered a candidate derivative work"""
    imgs = ALL_IMAGES['memed']
    h1 = imagehash(imgs[0])[imgs[0]]
    h2 = imagehash(imgs[1])[imgs[1]]
    dist = h1 - h2
    assert dist > THRESHOLD_IDENTITY and dist < THRESHOLD_SIMILARITY
