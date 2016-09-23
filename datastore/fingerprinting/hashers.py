import uuid
import subprocess

from PIL import Image


def random(imgfile):
    """This 'strategy' simply returns a unique random value and should always fail to
    assign the same hash to two different images. This is to ensure that our tests are honest"""
    return uuid.uuid4()


def phash(imgfile):
    # This is a common algorithm but is deliberately not included in this package
    # as it is no longer maintained and considered to have unaddressed security
    # flaws: https://bugs.debian.org/cgi-bin/bugreport.cgi?bug=751916
    raise NotImplementedError("Not intending to include")
