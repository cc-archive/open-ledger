import json
import os


def load_json_data(datafile):
    """Load testing data in JSON format relative to the path where the test lives"""
    dir_path = os.path.dirname(os.path.realpath(__file__))
    return json.loads(open(os.path.join(dir_path, datafile)).read())
