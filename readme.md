ssm-connect is a wrapper for the new AWS session-manager-plugin which allows you to start a session on any ssm enabled machines within your AWS account from within your terminal. With the awscli tool, you are required to specify the instance-id for the instance you wish to connect to, while this script will allow you to simply pass the name of the instance and it will look up the instance-id and connect you to the machine.

# Requirements

- Python 2.7 (Should be compatible with Python3)
- awscli
- boto3
- ssm session-manager-plugin

boto3 and awscli can be installed with pip.

```
pip install boto3 --user
pip install awscli --user
```

AWS has documentation on how to install the session-manager-plugin here:

https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-install-plugin.html

# Usage

The script will use your aws credentials file to connect to AWS, and will use the `default` profile if none is specified. If you have multiple profiles set up in your credentials file, use the `-p` flag to tell the script which profile to use.

```
[~]# ssm-connect --help
usage: ssm-connect [-h] -n NAME [-p PROFILE]

optional arguments:
  -h, --help            show this help message and exit
  -n NAME, --name NAME  Instance name
  -p PROFILE, --profile PROFILE
                        AWS credentials profile name
```

```
[~]# ssm-connect -n example -p ex_profile


Starting session with SessionId: botocore-session

$
```
