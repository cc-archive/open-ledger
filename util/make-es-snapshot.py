from aws_requests_auth.aws_auth import AWSRequestsAuth
import requests
import os
import datetime

SNAPSHOT_DIR = 'ccsearch-snapshots'

# Run this just one time to register the specified cluster for manual
# backups. See the shared loader environment for env variables.

if __name__ == "__main__":
    auth = AWSRequestsAuth(aws_access_key=os.environ['ES_AWS_ACCESS_KEY_ID'],
                           aws_secret_access_key=os.environ['ES_AWS_SECRET_ACCESS_KEY'],
                           aws_host=os.environ['ES_CLUSTER_DNS'],
                           aws_region=os.environ['ES_REGION'],
                           aws_service='es')
    auth.encode = lambda x: bytes(x.encode('utf-8'))

    cluster_name = os.environ['ES_CLUSTER_DNS'].split('.')[0]
    snapshot_name = cluster_name + '-' + datetime.datetime.now().strftime("%Y-%m-%d")

    resp = requests.put('https://{}/_snapshot/{}/{}'.format(
                            os.environ['ES_CLUSTER_DNS'],
                            SNAPSHOT_DIR,
                            snapshot_name),
                            auth=auth)
    print(resp.content)
