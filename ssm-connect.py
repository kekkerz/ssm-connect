#!/usr/bin/env python
import argparse, boto3, subprocess, signal
from botocore.exceptions import ProfileNotFound

parser = argparse.ArgumentParser()
parser.add_argument('-n', '--name', help='Instance name', required=True)
parser.add_argument('-p', '--profile', help='AWS credentials profile name', default='default')
args = parser.parse_args()

class ssm:

    def __init__(self, profile):
        try:
            self.session = boto3.Session(profile_name='{}'.format(profile))
        except ProfileNotFound:
            raise Exception('Default profile not found. Specify config profile.')

        self.ec2_client = self.session.client('ec2')

    def get_instance_id(self, name):
        response = self.ec2_client.describe_instances(
            Filters=[
                {
                    'Name': 'tag:Name',
                    'Values': [
                        args.name
                    ]
                }
            ]
        )

        try:
            instances = response['Reservations'].pop()['Instances']
        except IndexError:
            raise Exception('No instances found')

        instance_count = len(instances)
        if instance_count > 1:
            raise Exception('Multiple instances found.')
        elif instance_count < 1:
            raise Exception('No instances found.')
        else:
            return instances.pop()['InstanceId']

    def start_connection(self, instance_id, profile):
        subprocess.call(['aws', 'ssm', 'start-session', '--target', '{}'.format(instance_id), '--profile', '{}'.format(profile)])

#Properly handle CTRL+C and preventing SIGINT from exiting python script
def handler(signum, frame):
    pass

signal.signal(signal.SIGINT, handler)
ssm = ssm(args.profile)
instance_id = ssm.get_instance_id(args.name)
ssm.start_connection(instance_id, args.profile)
