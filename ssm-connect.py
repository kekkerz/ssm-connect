#!/usr/bin/env python
import argparse, boto3, subprocess, signal, readline, os
from ConfigParser import ConfigParser
from ConfigParser import NoOptionError
from ConfigParser import NoSectionError
from botocore.exceptions import ProfileNotFound
from botocore.exceptions import ClientError

parser = argparse.ArgumentParser()
parser.add_argument('-n', '--name', help='Instance name', required=True)
parser.add_argument('-p', '--profile', help='AWS credentials profile name', default='default')
args = parser.parse_args()

aws_config = ConfigParser()
aws_config.read([os.path.join(os.path.expanduser('~'), '.aws/config')])
mfa_config = ConfigParser()
mfa_config.read([os.path.join(os.path.expanduser('~'), '.aws/mfa_config')])

class ssm:

    def __init__(self, name, profile):
        self.profile = profile
        self.name = name
        self.instance_id = None
        try:
            boto3.session.Session(profile_name=self.profile).client('ssm').describe_instance_information()
        except ClientError:
            try:
                self.role_arn = aws_config.get('profile {}'.format(self.profile), 'role_arn')
                self.profile_region = aws_config.get('profile {}'.format(self.profile), 'region')
            except NoSectionError:
                try:
                    self.role_arn = aws_config.get(self.profile, 'role_arn')
                    self.profile_region = aws_config.get(self.profile, 'region')
                except NoSectionError:
                    raise Exception('Unable to locate profile "{}"'.format(self.profile))


            self.current_user = os.getenv('USER')
            self.mfa_token_section = '{}-{}'.format(self.current_user, self.profile)
            try:
                self.mfa_serial = mfa_config.get(self.current_user, 'mfa_serial')
            except (NoSectionError, NoOptionError):
                self.mfa_serial = raw_input('MFA ARN serial not found in config. Enter MFA ARN: ')
                if not mfa_config.has_section(self.current_user):
                    mfa_config.add_section(self.current_user)
                mfa_config.set(self.current_user, 'mfa_serial', self.mfa_serial)
                mfa_config.write(open(os.path.join(os.path.expanduser('~'), '.aws/mfa_config'), 'w'))

            try:
                self.get_mfa_keys()
                self.verify_credentials()
            except (NoSectionError, NoOptionError, ClientError):
                self.assume_role()
            finally:
                self.set_aws_session()

        except ProfileNotFound:
            raise Exception('Default profile not found. Specify config profile.')
        else:
            self.session = boto3.Session(profile_name='{}'.format(self.profile))

        self.get_instance_id()
        self.start_connection()

    def verify_credentials(self):
        boto3.client(
            'ssm',
            aws_access_key_id=self.access_key_id,
            aws_secret_access_key=self.secret_access_key,
            aws_session_token=self.session_token,
            region_name=self.profile_region
        ).describe_instance_information()

    def set_aws_session(self):
        self.session = boto3.Session(
            aws_access_key_id=self.access_key_id,
            aws_secret_access_key=self.secret_access_key,
            aws_session_token=self.session_token,
            region_name=self.profile_region
        )

    def get_mfa_keys(self):
        self.access_key_id = mfa_config.get(self.mfa_token_section, 'access_key_id')
        self.secret_access_key = mfa_config.get(self.mfa_token_section, 'secret_access_key')
        self.session_token = mfa_config.get(self.mfa_token_section, 'session_token')

    def assume_role(self):
        self.sts = boto3.client('sts')
        self.mfa_code = raw_input('Enter MFA code: ')


        response = self.sts.assume_role(
            RoleArn=self.role_arn,
            RoleSessionName='{}_Session'.format(self.current_user),
            DurationSeconds=900,
            SerialNumber=self.mfa_serial,
            TokenCode=self.mfa_code
        )

        try:
            self.access_key_id = response['Credentials']['AccessKeyId']
            self.secret_access_key = response['Credentials']['SecretAccessKey']
            self.session_token = response['Credentials']['SessionToken']
            if not mfa_config.has_section(self.mfa_token_section):
                mfa_config.add_section(self.mfa_token_section)
            mfa_config.set(self.mfa_token_section, 'access_key_id', self.access_key_id)
            mfa_config.set(self.mfa_token_section, 'secret_access_key', self.secret_access_key)
            mfa_config.set(self.mfa_token_section, 'session_token', self.session_token)
            mfa_config.write(open(os.path.join(os.path.expanduser('~'), '.aws/mfa_config'), 'w'))
        except KeyError:
            raise Exception('Error assuming role "{}"'.format(self.role_arn))

    def get_instance_id(self):
        self.ssm = self.session.client('ssm')
        response = self.ssm.describe_instance_information(
            Filters=[
                {
                    'Key': 'tag:Name',
                    'Values': [
                        self.name
                    ]
                }
            ]
        )

        instances = response['InstanceInformationList']
        instance_count = len(instances)

        if instance_count > 1:
            raise Exception('Multiple instances found.')
        elif instance_count < 1:
            raise Exception('No instances found.')
        else:
            self.instance_id = instances.pop()['InstanceId']

    def start_connection(self):
        try:
            os.environ['AWS_ACCESS_KEY_ID'] = self.access_key_id
            os.environ['AWS_SECRET_ACCESS_KEY'] = self.secret_access_key
            os.environ['AWS_SESSION_TOKEN'] = self.session_token
            os.environ['AWS_DEFAULT_REGION'] = self.profile_region
            subprocess.call(['aws', 'ssm', 'start-session', '--target', '{}'.format(self.instance_id)])
        except AttributeError:
            subprocess.call(['aws', 'ssm', 'start-session', '--target', '{}'.format(self.instance_id), '--profile', '{}'.format(self.profile)])

#Properly handle CTRL+C and preventing SIGINT from exiting ssm session
def handler(signum, frame):
    pass

signal.signal(signal.SIGINT, handler)
ssm = ssm(args.name, args.profile)
