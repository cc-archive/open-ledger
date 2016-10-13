#!/bin/bash

# This script expects to be run on a remote EC2 host deployed via Elastic Beanstalk like:
# eb ssh --command=/opt/python/current/app/load-all-data.sh

IMAGES_DATA=openimages/images_2016_08/validation/images.csv
TAGS_DATA=openimages/dict.csv
IMAGES_TAGS_DATA=openimages/human_ann_2016_08/validation/labels.csv

cd /opt/python/current/app/
source /opt/python/current/env

/opt/python/run/venv/bin/python database_import.py $IMAGES_DATA openimages images --filesystem s3
/opt/python/run/venv/bin/python database_import.py $TAGS_DATA openimages tags --filesystem s3
/opt/python/run/venv/bin/python database_import.py $IMAGES_TAGS_DATA openimages image-tags --filesystem s3
