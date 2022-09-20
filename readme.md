ssm-connect is a wrapper for the new AWS session-manager-plugin which allows you to start a session on any ssm enabled machines within your AWS account from within your terminal. With the awscli tool, you are required to specify the instance-id for the instance you wish to connect to, while this script will allow you to simply pass the name of the instance and it will look up the instance-id and connect you to the machine.

This script supports MFA and shares session cache with AWS-CLI. Simply add your MFA ARN to your config profile in `~/.aws/config` using the `mfa_serial` parameter.

https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html

This script also supports the use of SSO with aws-cli. Follow the directions below to get SSO set up in your aws config, and ssm-connect will be able to use it's cache to authenticate. Currently, you will still need to use `aws sso login --profile {profile_name}` for the initial authentication to an account. 

https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-sso.html#sso-configure-profile

# Requirements

- Python 3
- awscli (SSO requires awscli v2)
- boto3
- argparse
- ssm session-manager-plugin

boto3, awscli, and argparse can be installed with pip.

```
pip install boto3 --user
pip install argparse --user
pip install awscli --user
```

AWS has documentation on how to install the session-manager-plugin here:

https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-install-plugin.html

# Usage

The script will use your aws credentials file to connect to AWS, and will use the `default` profile if none is specified. If you have multiple profiles set up in your credentials file, use the `-p` flag to tell the script which profile to use.

```
[~]# ssm-connect --help
usage: ssm-connect [-h] (-n NAME | -i INSTANCE | -t TAGS) [-c COMMAND] [-p PROFILE] [-l LOCAL] [-r REMOTE]

optional arguments:
  -h, --help            show this help message and exit
  -n NAME, --name NAME  Instance name
  -i INSTANCE, --instance INSTANCE
                        Instance ID
  -t TAGS, --tags TAGS  Tags to target multiple instances
  -c COMMAND, --command COMMAND
                        Command to run on instance
  -p PROFILE, --profile PROFILE
                        AWS credentials profile name
  -l LOCAL, --local LOCAL
                        Local port used for reverse tunneling
  -r REMOTE, --remote REMOTE
                        Remote port used for reverse tunneling
```

```
[~]# ssm-connect -n example -p ex_profile


Starting session with SessionId: botocore-session

$
```

The script also supports port forwarding. E.g.
```
[~]# ssm-connect -n example -p ex_profile -l <local_bind_port> -r <remote_bind_port>

Starting session with SessionId: <session_id>
Port <local_bind_port> opened for sessionId <session_id>.

```

Running commands on remote instances:
```
[~]# ssm-connect -n example -c hostname -p ex_profile
##### i-xxxxxxxxxxxxxxxxx:

example_host

[~]# ssm-connect -t '[{"Key": "tag:Name", "Values":["example"]}]' -c hostname -p ex_profile
##### i-xxxxxxxxxxxxxxxxx:

example_host
```
