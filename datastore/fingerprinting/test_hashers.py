import os

from hashers import *

IMAGE_DIR = 'samples'

# A set of pairs of images that all begin with the same string, indicating what
# has changed between them
ALL_IMAGES = []

IMAGE_TESTS = ('cropped',  # One image is a cropped version of the other
               'providers',  # Same work, same dimensions, but sourced from
                             # two different providers (different binaries)
               )

for test in IMAGE_TESTS:
    pair = [os.path.join(IMAGE_DIR, f) for f in os.listdir(IMAGE_DIR) if f.startswith(test)]
    ALL_IMAGES.append(pair)

def test_random():
    """Images with the random hasher should _always_ fail to return the same hash"""
    for imgset in ALL_IMAGES:
        assert random(imgset[0]) != random(imgset[1])

def test_simple():
    """Images with the simple hasher should be within a certain threshold"""
    imgs = ALL_IMAGES[0]
    img1 = simple(imgs[0])
    img2 = simple(imgs[1])
    print(_hamming_distance(img1, img2))
    raise Exception
