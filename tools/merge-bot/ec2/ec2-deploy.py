import os
import json
import time
import zipfile
import boto3


def create_ec2_instance(instance_role, key_name, user_data):
    ec2_client = boto3.client('ec2')
    response = ec2_client.run_instances(
        BlockDeviceMappings=[
            {
                'DeviceName': '/dev/xvda',
                'Ebs': {

                    'DeleteOnTermination': True,
                    'VolumeSize': 8,
                    'VolumeType': 'gp2'
                },
            },
        ],
        KeyName=key_name,
        UserData=user_data,
        ImageId='ami-0cd3dfa4e37921605',
        InstanceType='t2.micro',
        MaxCount=1,
        MinCount=1,
        Monitoring={
            'Enabled': False
        },
        SecurityGroupIds=[
            'sg-00f3b71d4b6021b03',
        ]
    )
    return response


def create_ssm_parameters(ssm_parameters):
    ssm_client = boto3.client('ssm')
    print(ssm_parameters)
    for name in ssm_parameters:
        response = ssm_client.put_parameter(
            Name=name,
            Value=ssm_parameters[name],
            Type='SecureString',
            Overwrite=True
        )
    return response


def create_key_pair_for_ec2(key_name):
    ec2_client = boto3.client('ec2')
    response = ec2_client.create_key_pair(KeyName=key_name)

    with open('{}.pem'.format(key_name), 'w') as key:
        key.write(response['KeyMaterial'])
    return response


def create_lambda_function(function_role, function_name, ec2_instance_id, queue_name):
    lambda_client = boto3.client('lambda')

    zipf = zipfile.ZipFile('lambda.zip', 'w')
    zipf.write('lambda-function.py')
    zipf.close()

    with open('./lambda.zip', 'rb') as lambda_zip:
        lambda_code = lambda_zip.read()

    response = lambda_client.create_function(
        FunctionName=function_name,
        Runtime='python3.6',
        Role=function_role,
        Handler='lambda-function.handler',
        Code={'ZipFile': lambda_code},
        Environment={
            'Variables': {
                'INSTANCE_ID': ec2_instance_id,
                'QUEUE_NAME': queue_name
            }
        }
    )
    # TODO: connect api gateway to lambda
    '''lambda_client.add_permission(
        FunctionName=function_name,
        StatementId=function_name + "-ID",
        Action="lambda:InvokeFunction",
        Principal="apigateway.amazonaws.com",
        SourceArn="arn:aws:execute-api:" + self.region + ":" + self.getAccountId() + ":" + apiId + "/*/" + httpMethod + "/" + httpPath,
        # SourceAccount='string',
        # Qualifier='string'

    )'''
    os.remove('lambda.zip')
    return response


def create_role(role_name, service, role_policies):
    iam_client = boto3.client('iam')

    assume_role_policy_document = json.dumps({
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": service
                },
                "Action": "sts:AssumeRole"
            }
        ]
    })

    response = iam_client.create_role(
        Path='/service-role/',
        RoleName=role_name,
        AssumeRolePolicyDocument=assume_role_policy_document
    )
    for policy in role_policies:
        iam_client.attach_role_policy(
            RoleName=response['Role']['RoleName'],
            PolicyArn=policy
        )
    return response


def create_api_gateway(function_name):
    apigateway_client = boto3.client('apigateway')
    # TODO: create api gateway


def create_sqs(queue_name):
    sqs_client = boto3.client('sqs')
    response = sqs_client.create_queue(
        QueueName=queue_name
    )
    return response


def main():
    print('Starting deployment process.')
    key_name = 'github-bot-key'
    queue_name = 'github-bot-queue'
    user_data = open('/'.join(os.path.realpath(__file__).split('/')[:-1]) + '/ec2-script.sh').read()
    roles_for_lambda = ['arn:aws:iam::aws:policy/AmazonSQSFullAccess',
                        'arn:aws:iam::aws:policy/AmazonEC2FullAccess',
                        'arn:aws:iam::aws:policy/AWSLambdaExecute']
    role_name_lambda = 'github-bot-lambda-role'
    roles_for_ec2 = ['arn:aws:iam::aws:policy/AmazonSQSFullAccess',
                     'arn:aws:iam::aws:policy/service-role/AmazonEC2RoleforSSM']
    role_name_ec2 = 'github-bot-ec2-role'
    lambda_name = 'github-bot-lambda'
    ssm_parameters = {
        'QUEUE_NAME': queue_name,
        'SHUTDOWN_TIME': '60',
        'GITHUB_TOKEN_FOR_BOT': os.getenv('GITHUB_TOKEN_FOR_BOT')
    }

    create_sqs(queue_name)
    print('SQS queue {} created'.format(queue_name))

    create_key_pair_for_ec2(key_name)
    print('Key pair for EC2 {} created'.format(key_name))

    ssm_response = create_ssm_parameters(ssm_parameters)
    for name in ssm_parameters:
        print('SSM parameter {} created'.format(name))

    iam_response = create_role(role_name_ec2, 'ec2.amazonaws.com', roles_for_ec2)
    role_arn = iam_response['Role']['Arn']
    print('IAM role {} created'.format(role_name_ec2))

    ec2_response = create_ec2_instance(role_name_ec2, key_name, user_data)
    instance_id = ec2_response['Instances'][0]['InstanceId']
    print('EC2 instance (id: {}) created'.format(instance_id))

    iam_response = create_role(role_name_lambda, 'lambda.amazonaws.com', roles_for_lambda)
    role_arn = iam_response['Role']['Arn']
    print('IAM role {} created'.format(role_name_lambda))

    time.sleep(10)

    lambda_response = create_lambda_function(role_arn, lambda_name, instance_id, queue_name)
    print('Lambda function {} created'.format(lambda_name))

    print('Deployment process succeeded.')


if __name__ == "__main__":
    main()
