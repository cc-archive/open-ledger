from aws_requests_auth.aws_auth import AWSRequestsAuth
import requests
import os

from . import SNAPSHOT_DIR

# Run this just one time to register the specified cluster for manual
# backups. See the shared loader environment for env variables.

if __name__ == "__main__":
    auth = AWSRequestsAuth(aws_access_key=os.environ['ES_AWS_ACCESS_KEY_ID'],
                           aws_secret_access_key=os.environ['ES_AWS_SECRET_ACCESS_KEY'],
                           aws_host=os.environ['ES_CLUSTER_DNS'],
                           aws_region=os.environ['ES_REGION'],
                           aws_service='es')
    auth.encode = lambda x: bytes(x.encode('utf-8'))

    data = bytes('{"type": "s3","settings": { ' + \
            '"bucket": "' + os.environ['ES_MANUAL_SNAPSHOT_S3_BUCKET'] + \
            '","region": "' + os.environ['ES_REGION'] + \
            '","role_arn": "' + os.environ['ES_IAM_MANUAL_SNAPSHOT_ROLE_ARN'] + \
            '"}}', encoding="utf-8")

    resp = requests.post('https://{}/_snapshot/{}'.format(os.environ['ES_CLUSTER_DNS'],
                                                          SNAPSHOT_DIR),
                         auth=auth,
                         data=data)
    print(resp.content)
