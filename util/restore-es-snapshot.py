from aws_requests_auth.aws_auth import AWSRequestsAuth
import requests
import sys
import os
import datetime

SNAPSHOT_DIR = 'ccsearch-snapshots'

# Run this just one time to register the specified cluster for manual
# backups. See the shared loader environment for env variables.

if __name__ == "__main__":
    snapshot_name = sys.argv[1]
    to_host = sys.argv[2]

    auth = AWSRequestsAuth(aws_access_key=os.environ['ES_AWS_ACCESS_KEY_ID'],
                           aws_secret_access_key=os.environ['ES_AWS_SECRET_ACCESS_KEY'],
                           aws_host=to_host,
                           aws_region=os.environ['ES_REGION'],
                           aws_service='es')
    auth.encode = lambda x: bytes(x.encode('utf-8'))



    print("Restoring snapshot {} to {}".format(snapshot_name, to_host))

    resp = requests.post('https://{}/_snapshot/{}/{}/_restore'.format(to_host,
                                                                      SNAPSHOT_DIR,
                                                                      snapshot_name,
                                                                      ),
                         auth=auth)
    print(resp.content)
