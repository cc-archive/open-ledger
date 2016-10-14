import os
import time
import boto3
import botocore
import logging

from fabric.api import local, settings, abort, run, cd, env, put, sudo, hosts
from fabric.contrib.console import confirm

timestamp="release-%s" % int(time.time() * 1000)

CODE_DIR = '/home/liza/open-ledger'
CURRENT_BRANCH = 'master'

DEBUG = False

AMI = 'ami-27612947'
TAG = 'open-ledger-loader'

console = logging.StreamHandler()
log = logging.getLogger(__name__)
log.addHandler(console)
log.setLevel(logging.DEBUG)

def launchloader():
    """Launch an EC2 instance with the loader"""
    instance = None
    resource, client = _init_ec2()
    try:
        instance = _get_running_instance(resource, client)
        print(instance.public_ip_address)
    except:
        raise
    finally:
        # Stop it if it's running
        #instance.stop()
        pass

def _get_running_instance(resource, client):
    instance_type = 'r3.large'
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
                log.debug("Starting previously stopped instance")
                instance = i
                instance.start()
                break
        if not instance:
            log.debug("No stopped instances found; starting a brand new one...")
            instance = resource.create_instances(MinCount=1, MaxCount=1, InstanceType=instance_type, ImageId=AMI)[0]
            instance.wait_until_running()
            log.debug("Adding tag %s", TAG)
            instance.create_tags(Tags=[{'Key': 'Name', 'Value': TAG}])
            log.debug("Instance started: %r", instance)
    return instance

def _init_ec2():
    AMI = 'ami-27612947'
    session = boto3.Session(profile_name='cc-openledger')
    resource = session.resource('ec2', region_name='us-west-1')
    client = session.client('ec2', region_name='us-west-1')
    return resource, client

def deploy():
    with cd(CODE_DIR):
        run('git pull origin ' + CURRENT_BRANCH)
        run('./venv/bin/pip install -r requirements.txt')
        run('npm install')
        run('NODE_ENV=production node_modules/.bin/webpack')
    restart_host()

def restart_host():
    sudo('service openledger restart', shell=False)
