import os
import time
import boto3
import botocore
import logging

import fabtools
from fabric.api import local, settings, abort, run, cd, env, put, sudo, hosts
from fabric.contrib.console import confirm
from fabric.exceptions import NetworkError

import database_import

timestamp="release-%s" % int(time.time() * 1000)

CODE_DIR = '/home/liza/open-ledger'
CURRENT_BRANCH = 'master'

DEBUG = False

TAG = 'open-ledger-loader'
DB_TAG = 'open-ledger'
AMI = os.environ['OPEN_LEDGER_LOADER_AMI']
KEY_NAME = os.environ['OPEN_LEDGER_LOADER_KEY_NAME']
SECURITY_GROUPS = os.environ['OPEN_LEDGER_LOADER_SECURITY_GROUPS'].split(',')
REGION = os.environ['OPEN_LEDGER_REGION']
ACCOUNT_NUMBER = os.environ['OPEN_LEDGER_ACCOUNT']

DB_PASSWORD = os.environ['OPEN_LEDGER_DATABASE_PASSWORD']

#INSTANCE_TYPE = 'r3.large'
INSTANCE_TYPE = 't2.micro'

console = logging.StreamHandler()
log = logging.getLogger(__name__)
log.addHandler(console)
log.setLevel(logging.DEBUG)

log.debug("Starting up with ami=%s, key=%s", AMI, KEY_NAME)

class LoaderException(Exception):
    pass

def launchloader():
    """Launch an EC2 instance with the loader"""
    instance = None
    resource, client = _init_ec2()
    try:
        instance = _get_running_instance(resource, client)
        deploy_code(instance.public_ip_address)
        load_data_from_instance(instance)
    except LoaderException as e:
        log.exception(e)
        instance.terminate()
    except:
        raise
    finally:
        # Stop it if it's running
        #instance.stop()
        pass

def load_data_from_instance(instance):
    """Call a loading job from an instance"""
    database = _get_running_database()
    image_data_large = 'openimages/images_2016_08/train/images.csv'
    with settings(host_string="ec2-user@" + instance.public_ip_address):
        with cd('open-ledger'):
            run('./venv/bin/python database_import.py {image_data_large} openimages images --filesystem s3'.format(image_data_large=image_data_large))

def deploy_code(host_string):
    max_retries = 20
    retries = 0
    with settings(host_string="ec2-user@" + host_string):
        while True:
            try:
                fabtools.require.git.working_copy('https://github.com/creativecommons/open-ledger.git')
                with cd('open-ledger'):
                    run('virtualenv venv --python=python3 -q')
                    run('./venv/bin/pip install --upgrade pip -q')
                    run('./venv/bin/pip install -r loader-requirements.txt -q')
                    break
            except NetworkError:
                time.sleep(5)
                retries += 1
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

def _get_running_database():
    """Get a single RDS instance we can connect to."""
    client = _init_rds()
    resp = client.describe_db_instances()
    database = {}
    for r in resp['DBInstances']:
        identifier = r['DBInstanceIdentifier']
        resource_identifier = "arn:aws:rds:{}:{}:db:{}".format(REGION, ACCOUNT_NUMBER, identifier)
        tags = client.list_tags_for_resource(ResourceName=resource_identifier)['TagList']
        for tag in tags:
            if tag.get('Key') == 'elasticbeanstalk:environment-name':
                environment_name = tag.get('Value')
                if environment_name == 'open-ledger-dev':
                    # This is the one we want, finally, geez who made this API
                    database['host'] = r['Endpoint']['Address']
                    database['port'] = r['Endpoint']['Port']
                    database['name'] = r['DBName']
                    database['user'] = r['MasterUsername']
                    database['password'] = DB_PASSWORD
                    return database

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
        # Pick up a stopped instance and start it
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
            log.debug("No stopped instances found; starting a brand new one...")
            instance = resource.create_instances(MinCount=1, MaxCount=1,
                                                 SecurityGroups=SECURITY_GROUPS,
                                                 KeyName=KEY_NAME,
                                                 InstanceType=INSTANCE_TYPE,
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

# Legacy deployment mechanism for Digital Ocean hosts
def deploy():
    with cd(CODE_DIR):
        run('git pull origin ' + CURRENT_BRANCH)
        run('./venv/bin/pip install -r requirements.txt -q')
        run('npm install')
        run('NODE_ENV=production node_modules/.bin/webpack')
    restart_host()

def restart_host():
    sudo('service openledger restart', shell=False)

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
