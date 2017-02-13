from aws_requests_auth.aws_auth import AWSRequestsAuth
import requests
import os
import datetime
import json

SNAPSHOT_DIR = 'ccsearch-snapshots'

# List all ES snapshots for this domain

if __name__ == "__main__":
    auth = AWSRequestsAuth(aws_access_key=os.environ['ES_AWS_ACCESS_KEY_ID'],
                           aws_secret_access_key=os.environ['ES_AWS_SECRET_ACCESS_KEY'],
                           aws_host=os.environ['ES_CLUSTER_DNS'],
                           aws_region=os.environ['ES_REGION'],
                           aws_service='es')
    auth.encode = lambda x: bytes(x.encode('utf-8'))

    print("Listing available snapshots for {}".format(os.environ['ES_CLUSTER_DNS']))
    resp = requests.get('https://{}/_snapshot/{}/_all'.format(os.environ['ES_CLUSTER_DNS'],
                                                              SNAPSHOT_DIR),
                         auth=auth)
    content = resp.json()
    print(json.dumps(content, indent=4))
