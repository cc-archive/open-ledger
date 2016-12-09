import os
import time
import boto3
import botocore
import logging

import fabtools
from fabric.api import local, settings, abort, run, cd, env, put, sudo, hosts
from fabric.context_managers import shell_env
from fabric.contrib.console import confirm
from fabric.exceptions import NetworkError

timestamp="release-%s" % int(time.time() * 1000)

DEBUG = False

TAG = 'open-ledger-loader'
DB_TAG = 'open-ledger'
AMI = os.environ['OPEN_LEDGER_LOADER_AMI']
KEY_NAME = os.environ['OPEN_LEDGER_LOADER_KEY_NAME']
SECURITY_GROUPS = os.environ['OPEN_LEDGER_LOADER_SECURITY_GROUPS'].split(',')
REGION = os.environ['OPEN_LEDGER_REGION']
ACCOUNT_NUMBER = os.environ['OPEN_LEDGER_ACCOUNT']
AWS_ACCESS_KEY_ID = os.environ['OPEN_LEDGER_ACCESS_KEY_ID']
AWS_SECRET_ACCESS_KEY = os.environ['OPEN_LEDGER_SECRET_ACCESS_KEY']
ELASTICSEARCH_URL = os.environ['OPEN_LEDGER_ELASTICSEARCH_URL']
API_500PX_KEY = os.environ.get('API_500PX_KEY')
API_500PX_SECRET = os.environ.get('API_500PX_SECRET')
API_RIJKS = os.environ.get('API_RIJKS')
FLICKR_KEY = os.environ.get('FLICKR_KEY')
FLICKR_SECRET = os.environ.get('FLICKR_SECRET')
NYPL_KEY = os.environ.get('NYPL_KEY')
LOG_FILE = '/tmp/app.log'

DATASOURCES = {
    'openimages-full': {
        'action': 'load-from-file',
        'name': 'openimages-full',
        'source': 'openimages',
        'filesystem': 's3',
        'filepath': 'openimages/images_2016_08/train/images.csv',
        'datatype': 'images'},
    'openimages-small': {
        'action': 'load-from-file',
        'name': 'openimages-small',
        'source': 'openimages',
        'filesystem': 's3',
        'filepath': 'openimages/images_2016_08/validation/images.csv',
        'datatype': 'images'},
    'openimages-tags': {
        'action': 'load-from-file',
        'name': 'openimages-tags',
        'source': 'openimages',
        'filesystem': 's3',
        'filepath': 'openimages/dict.csv',
        'datatype': 'tags'},
    'openimages-human-image-tags': {
        'action': 'load-from-file',
        'name': 'openimages-human-image-tags',
        'source': 'openimages',
        'filesystem': 's3',
        'filepath': 'openimages/human_ann_2016_08/validation/labels.csv',
        'datatype': 'image-tags'},
    'openimages-machine-image-tags': {
        'action': 'load-from-file',
        'name': 'openimages-machine-image-tags',
        'source': 'openimages',
        'filesystem': 's3',
        'filepath': 'openimages/machine_ann_2016_08/validation/labels.csv',
        'datatype': 'image-tags'},
    'searchindex': {
        'action': 'reindex',
        'name': 'searchindex',
        },
    'rijks': {
        'action': 'load-from-provider',
        'name': 'load-rijks',
        'provider': 'rijks',
    },
    'nypl': {
        'action': 'load-from-provider',
        'name': 'load-nypl',
        'provider': 'nypl',
    },
    '500px': {
        'name': 'load-500px',
        'action': 'load-from-provider',
        'provider': '500px',
    },
    'wikimedia': {
        'name': 'load-wikimedia',
        'action': 'load-from-provider',
        'provider': 'wikimedia',
    },
    'sync': {
        'action': 'sync',
        'name': 'sync',
    }
}

if not env.get('flags'):
    env.flags = ""

# Load the "small" image datasource by default
# fab --set datasource=openimages-full
if env.get('datasource'):
    env.datasource=DATASOURCES[env.datasource]
else:
    env.datasource=DATASOURCES['openimages-small']

# Override from the command line as fab --set instance_type=r3.large
# This default is here to try to use the free tier whenever possible
if not env.get('instance_type'):
    env.instance_type = 't2.micro'

# Override the database instance or use the default
if not env.get('database_id'):
    env.database_id = 'openledger-db-1'

# Which branch should we check out on the loader?
if not env.get('branch'):
    env.branch = 'master'

# Run with nohup for long-running jobs we know will work?
if env.get('with_nohup'):
    env.with_nohup = True
else:
    env.with_nohup = False

# Force spinning up a new host (when other jobs are running)
if env.get('force_new'):
    env.force_new = True
else:
    env.force_new = False

console = logging.StreamHandler()
log = logging.getLogger(__name__)
log.addHandler(console)
log.setLevel(logging.DEBUG)

log.debug("Starting up with ami=%s, key=%s, db=%s", AMI, KEY_NAME, env.database_id)

class LoaderException(Exception):
    pass

def launchloader():
    """Launch an EC2 instance with the specified loader"""
    instance = None
    resource, client = _init_ec2()
    try:
        if env.force_new:
            instance = _start_new_instance(resource, client)
        else:
            instance = _get_running_instance(resource, client)
        # Name the instance after the datasource
        instance.create_tags(Tags=[{'Key': 'Name', 'Value': env.datasource['name']}])
        deploy_code(instance.public_ip_address)
        load_data_from_instance(instance)
    except LoaderException as e:
        log.exception(e)
        if instance:
            instance.terminate()
    except Exception as e:
        log.exception(e)
        if instance:
            instance.terminate()
        raise
    finally:
        # Stop it if it's running, unless we set nohup
        if instance and not env.with_nohup:
            instance.stop()
        pass

def load_data_from_instance(instance):
    """Call a loading job from an instance"""

    with settings(host_string="ec2-user@" + instance.public_ip_address):
        with cd('open-ledger'):
            with shell_env(
                DJANGO_DATABASE_NAME=os.environ.get('DJANGO_DATABASE_NAME'),
                DJANGO_DATABASE_PORT=os.environ.get('DJANGO_DATABASE_PORT'),
                DJANGO_DATABASE_HOST=os.environ.get('DJANGO_DATABASE_HOST'),
                DJANGO_DATABASE_USER=os.environ.get('DJANGO_DATABASE_USER'),
                DJANGO_DATABASE_PASSWORD=os.environ.get('DJANGO_DATABASE_PASSWORD'),
                AWS_SECRET_ACCESS_KEY=AWS_SECRET_ACCESS_KEY,
                AWS_ACCESS_KEY_ID=AWS_ACCESS_KEY_ID,
                ELASTICSEARCH_URL=ELASTICSEARCH_URL,
                API_500PX_KEY=API_500PX_KEY,
                API_500PX_SECRET=API_500PX_SECRET,
                API_RIJKS=API_RIJKS,
                FLICKR_KEY=FLICKR_KEY,
                FLICKR_SECRET=FLICKR_SECRET,
                LOG_FILE=LOG_FILE,
                NYPL_KEY=NYPL_KEY,
                DJANGO_SECRET_KEY=os.environ.get('DJANGO_SECRET_KEY')
                ):

                env.datasource['flags'] = env.flags
                env.datasource['before_args'] = 'screen -d -m ' if env.with_nohup else ""

                # Run any migrations first
                run('./venv/bin/python manage.py migrate')

                if env.datasource['action'] == 'reindex':
                    run('{before_args}./venv/bin/python manage.py indexer {flags}; sleep 1'.format(**env.datasource))
                elif env.datasource['action'] == 'load-from-file':
                    run('{before_args}./venv/bin/python manage.py loader {filepath} {source} {datatype} --filesystem {filesystem} --skip-checks {flags} ; sleep 1'.format(**env.datasource))
                elif env.datasource['action'] == 'load-from-provider':
                    run('{before_args}./venv/bin/python manage.py handlers {provider} {flags} ; sleep 1'.format(**env.datasource))
                elif env.datasource['action'] == 'sync':
                    run('{before_args}./venv/bin/python manage.py syncer {flags} ; sleep 1'.format(**env.datasource))

def deploy_code(host_string):
    max_retries = 20
    retries = 0
    log.debug("Waiting for instance to answer on ssh at {}".format(host_string))
    with settings(host_string="ec2-user@" + host_string):
        while True:
            try:
                fabtools.require.git.working_copy('https://github.com/creativecommons/open-ledger.git', branch=env.branch)
                with cd('open-ledger'):
                    run('virtualenv venv --python=python3 -q')
                    run('./venv/bin/pip install -r requirements.txt -q')
                    break
            except NetworkError:
                time.sleep(5)
                retries += 1
                log.debug("Retrying {} of {}...".format(retries, max_retries))
            if retries > max_retries:
                raise LoaderException("Timed out waiting for ssh")

def stop_loaders():
    """Terminate all loading instances that are running"""
    instance_ids, resource = _get_running_instances()
    [resource.Instance(i).stop() for i in instance_ids]
    log.info("Stopped instances %s", ", ".join(instance_ids)) if len(instance_ids) > 0 else None

def terminate_loaders():
    """Terminate all loading instances that are running"""
    instance_ids, resource = _get_running_instances()
    [resource.Instance(i).terminate() for i in instance_ids]
    log.info("Terminated instances %s", ", ".join(instance_ids)) if len(instance_ids) > 0 else None

def _get_running_instances():
    resource, client = _init_ec2()
    resp = client.describe_instances(Filters=[{'Name': 'tag:Name', 'Values': [TAG]},
                                              {'Name': 'instance-state-name', 'Values': ['running']}])
    instance_ids = []
    for r in resp['Reservations']:
        for i in r['Instances']:
            instance_ids.append(i['InstanceId'])
    if len(instance_ids) == 0:
        log.info("No running instances found")
    return instance_ids, resource


def _get_running_instance(resource, client):
    resp = client.describe_instances(Filters=[{'Name': 'tag:Name', 'Values': [TAG]},
                                              {'Name': 'instance-state-name', 'Values': ['running']}])
    instance = None
    instances = []
    for r in resp['Reservations']:
        for i in r['Instances']:
            instances.append(i)
    if len(instances) > 0:
        log.debug("Found %d running instances, returning %r", len(instances), instances[0]["InstanceId"])
        return resource.Instance(instances[0]['InstanceId'])
    else:
        return _start_new_instance(resource, client)

def _start_new_instance(resource, client):
    # Pick up a stopped instance and start it
    instance = None
    resp = client.describe_instances(Filters=[{'Name': 'tag:Name', 'Values': [TAG]},
                                          {'Name': 'instance-state-name', 'Values': ['stopped']}])
    for r in resp['Reservations']:
        for i in r['Instances']:
            instance = resource.Instance(i['InstanceId'])
            log.debug("Starting previously stopped instance %s", i['InstanceId'])
            instance.start()
            instance.wait_until_running()
            break
        if instance:
            break

    if not instance:
        log.debug("No stopped instances found; starting a brand new type %s instance...", env.instance_type)
        security_groups = SECURITY_GROUPS
        instance = resource.create_instances(MinCount=1, MaxCount=1,
                                             SecurityGroups=security_groups,
                                             KeyName=KEY_NAME,
                                             InstanceType=env.instance_type,
                                             UserData=user_data,
                                             ImageId=AMI)[0]
        instance.wait_until_running()
        log.debug("Adding tag %s", TAG)
        instance.create_tags(Tags=[{'Key': 'Name', 'Value': TAG}])
        log.debug("Instance started: %r", instance)
    return instance

def _init_aws():
    session = boto3.Session(profile_name='cc-openledger')
    return session

def _init_ec2():
    session = _init_aws()
    resource = session.resource('ec2', region_name='us-west-1')
    client = session.client('ec2', region_name='us-west-1')
    return resource, client

def _init_rds():
    session = _init_aws()
    client = session.client('rds', region_name='us-west-1')
    return client

# Configuration for EC2 startup
user_data = """
#cloud-config
repo_update: true
repo_upgrade: all

packages:
 - gcc
 - nodejs
 - git
 - python34
 - python34-virtualenv
 - postgresql93
 - postgresql93-devel
 - libjpeg-turbo-devel
"""
