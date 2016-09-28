import uuid
import subprocess

from PIL import Image

def hamming_distance(s1, s2):
    """Return the Hamming distance between equal-length sequences, a measure of hash similarity"""
    # Transform into a fixed-size binary string first
    s1bin = ' '.join('{0:08b}'.format(ord(x), 'b') for x in s1)
    s2bin = ' '.join('{0:08b}'.format(ord(x), 'b') for x in s2)
    if len(s1bin) != len(s2bin):
        raise ValueError("Undefined for sequences of unequal length")
    return sum(el1 != el2 for el1, el2 in zip(s1bin, s2bin))

def random(imgfile):
    """This 'strategy' simply returns a unique random value and should always fail to
    assign the same hash to two different images. This is to ensure that our tests are honest"""
    return str(uuid.uuid4())

def phash(imgfile):
    # This is a common algorithm but is deliberately not included in this package
    # as it is no longer maintained and considered to have unaddressed security
    # flaws: https://bugs.debian.org/cgi-bin/bugreport.cgi?bug=751916
    raise NotImplementedError("Not intending to include")

def blockhash(imgfile):
    # Algorithm from https://github.com/creativecommons/blockhash-python
    # This fails on images that are cropped/resized
    from blockhash import process_images
    options = {
        'quick': False,
        'bits': 16,
        'size': "256x256",
        'interpolation': 1,
        'debug': False,
    }
    return process_images([imgfile], options=options)
