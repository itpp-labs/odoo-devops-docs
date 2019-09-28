import os
import json
import time
from zipfile import ZipFile
import argparse
import boto3


def deploy_bot(github_token, deployment_info, info_filename):
    path_to_info_filename = '/'.join(os.path.realpath(__file__).split('/')[:-2]) + '/' + info_filename

    queue_name = deployment_info['queue_name']
    key_name = deployment_info['key_name']
    role_name_ec2 = deployment_info['role_name_ec2']
    role_name_lambda = deployment_info['role_name_lambda']
    lambda_name = deployment_info['lambda_name']
    instance_profile_name = deployment_info['instance_profile_name']
    git_author = deployment_info['git_author']
    hook_exists = deployment_info['hook_exists']
    hook_created = deployment_info['hook_created']

    print('Starting deployment process.')
    user_data = open('/'.join(os.path.realpath(__file__).split('/')[:-1]) + '/ec2-script.sh').read()
    role_policies_for_ec2 = ['arn:aws:iam::aws:policy/AmazonSQSFullAccess',
                             'arn:aws:iam::aws:policy/AmazonEC2FullAccess',
                             'arn:aws:iam::aws:policy/AWSLambdaExecute',
                             'arn:aws:iam::aws:policy/service-role/AmazonEC2RoleforSSM',
                             'arn:aws:iam::aws:policy/AmazonSSMFullAccess']
    deployment_info['role_policies_for_ec2'] = role_policies_for_ec2

    role_policies_for_lambda = ['arn:aws:iam::aws:policy/AmazonSQSFullAccess',
                                'arn:aws:iam::aws:policy/AmazonEC2FullAccess']
    deployment_info['role_policies_for_lambda'] = role_policies_for_lambda

    ssm_parameters = {
        'QUEUE_NAME': queue_name,
        'SHUTDOWN_TIME': '60',
        'GITHUB_TOKEN_FOR_BOT': github_token,
        'GIT_AUTHOR': git_author,
        'WEBHOOK_WHEN_PORTING_PR_EXISTS': hook_exists,
        'WEBHOOK_WHEN_PORTING_PR_CREATED': hook_created
    }
    deployment_info['ssm_parameters'] = ssm_parameters

    sqs_response = create_sqs(queue_name)
    print('SQS queue {} created'.format(queue_name))
    deployment_info['sqs_queue_url'] = sqs_response['QueueUrl']

    create_key_pair_for_ec2(key_name)
    print('Key pair for EC2 {} created'.format(key_name))

    create_ssm_parameters(ssm_parameters)
    for name in ssm_parameters:
        print('SSM parameter {} created'.format(name))

    create_role(role_name_ec2, 'ec2.amazonaws.com', role_policies_for_ec2)
    print('IAM role {} created'.format(role_name_ec2))

    iam_response = create_instance_profile(instance_profile_name, role_name_ec2)
    instance_profile_arn = iam_response['InstanceProfile']['Arn']
    print('Instance profile {} created'.format(instance_profile_name))

    ec2_response = create_ec2_instance(instance_profile_name, instance_profile_arn, key_name, user_data)
    instance_id = ec2_response['Instances'][0]['InstanceId']
    print('EC2 instance (id: {}) created'.format(instance_id))
    deployment_info['ec2_instance_id'] = instance_id

    iam_response = create_role(role_name_lambda, 'lambda.amazonaws.com', role_policies_for_lambda)
    role_arn = iam_response['Role']['Arn']
    print('IAM role {} created'.format(role_name_lambda))

    time.sleep(10)

    create_lambda_function(role_arn, lambda_name, instance_id, queue_name)
    print('Lambda function {} created'.format(lambda_name))

    with open(path_to_info_filename, 'w') as fp:
        json.dump(deployment_info, fp, indent=4)
    print('Json file {} with deployment info is written'.format(info_filename))

    print('Deployment process succeeded.')


def remove_bot(info_filename):
    path_to_info_filename = '/'.join(os.path.realpath(__file__).split('/')[:-2]) + '/' + info_filename

    deployment_info = read_deploy_info(path_to_info_filename)
    queue_name = deployment_info['queue_name']
    key_name = deployment_info['key_name']
    path_to_key = '/'.join(os.path.realpath(__file__).split('/')[:-2]) + '/' + key_name + '.pem'

    role_name_ec2 = deployment_info['role_name_ec2']
    role_name_lambda = deployment_info['role_name_lambda']
    lambda_name = deployment_info['lambda_name']
    ec2_instance_id = deployment_info['ec2_instance_id']
    ssm_parameters = list(deployment_info['ssm_parameters'].keys())
    sqs_queue_url = deployment_info['sqs_queue_url']
    role_policies_for_ec2 = deployment_info['role_policies_for_ec2']
    role_policies_for_lambda = deployment_info['role_policies_for_lambda']
    instance_profile_name = deployment_info['instance_profile_name']

    sqs_client = boto3.client('sqs')
    ec2_client = boto3.client('ec2')
    lambda_client = boto3.client('lambda')
    ssm_client = boto3.client('ssm')

    print('Starting removal process.')

    sqs_client.delete_queue(QueueUrl=sqs_queue_url)
    print('SQS queue {} removed'.format(queue_name))

    ec2_client.delete_key_pair(KeyName=key_name)
    print('Key pair for EC2 {} removed'.format(key_name))

    ssm_client.delete_parameters(Names=ssm_parameters)
    for name in ssm_parameters:
        print('SSM parameter {} removed'.format(name))

    delete_instance_profile(instance_profile_name, role_name_ec2)
    print('Instance profile {} removed'.format(instance_profile_name))

    delete_role(role_name_ec2, role_policies_for_ec2)
    print('IAM role {} removed'.format(role_name_ec2))

    ec2_client.terminate_instances(InstanceIds=[ec2_instance_id])
    print('EC2 instance (id: {}) terminated'.format(ec2_instance_id))

    delete_role(role_name_lambda, role_policies_for_lambda)
    print('IAM role {} removed'.format(role_name_lambda))

    lambda_client.delete_function(FunctionName=lambda_name)
    print('Lambda function {} removed'.format(lambda_name))

    os.remove(path_to_key)
    print('Key file {} deleted'.format(info_filename))

    os.remove(path_to_info_filename)
    print('Json file {} with deployment info is deleted'.format(info_filename))

    print('Removal process succeeded.')


def read_deploy_info(info_filename):
    with open(info_filename, 'r') as fp:
        deployment_info = json.load(fp)
    return deployment_info


def create_ec2_instance(instance_profile_name, instance_profile_arn, key_name, user_data):
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
            'sg-ad82ddc1',
        ]
    )
    time.sleep(30)
    ec2_client.associate_iam_instance_profile(
        IamInstanceProfile={
            'Arn': instance_profile_arn,
            'Name': instance_profile_name
        },
        InstanceId=response['Instances'][0]['InstanceId']
    )

    return response


def create_ssm_parameters(ssm_parameters):
    ssm_client = boto3.client('ssm')
    for name in ssm_parameters:
        ssm_client.put_parameter(
            Name=name,
            Value=ssm_parameters[name],
            Type='SecureString',
            Overwrite=True
        )


def create_key_pair_for_ec2(key_name):
    ec2_client = boto3.client('ec2')
    response = ec2_client.create_key_pair(KeyName=key_name)

    path_to_key = '{}/{}.pem'.format('/'.join(os.path.realpath(__file__).split('/')[:-2]), key_name)

    with open(path_to_key, 'w') as key:
        key.write(response['KeyMaterial'])
    os.chmod(path_to_key, 0o400)

    return response


def create_lambda_function(function_role, function_name, ec2_instance_id, queue_name):
    lambda_client = boto3.client('lambda')

    path_to_lambda = '/'.join(os.path.realpath(__file__).split('/')[:-2]) + '/lambda-function.py'
    zipf = ZipFile('lambda.zip', 'w')
    zipf.write(path_to_lambda, os.path.basename(path_to_lambda))
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


def create_instance_profile(profile_name, role_name):
    iam_client = boto3.client('iam')
    iam = boto3.resource('iam')

    response = iam_client.create_instance_profile(
            InstanceProfileName=profile_name,
        Path='/'
    )

    instance_profile = iam.InstanceProfile(profile_name)

    instance_profile.add_role(
        RoleName=role_name
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


def delete_role(role_name, role_policies):
    iam_client = boto3.client('iam')
    for policy_arn in role_policies:
        iam_client.detach_role_policy(
            RoleName=role_name,
            PolicyArn=policy_arn
        )
    iam_client.delete_role(RoleName=role_name)


def delete_instance_profile(profile_name, role_name):
    iam = boto3.resource('iam')

    instance_profile = iam.InstanceProfile(profile_name)

    instance_profile.remove_role(
        RoleName=role_name
    )
    instance_profile.delete()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--github_token",
        help="Token from github account. If token not specified, it"
             " will be taken from GITHUB_TOKEN_FOR_BOT environmental variable.",
        default=os.getenv("GITHUB_TOKEN_FOR_BOT"))
    parser.add_argument(
        "--git_author",
        help="Author info to use in commits. If not specified, it"
             "will be taken from GIT_AUTHOR environmental variable.",
        default=os.getenv("GIT_AUTHOR"))
    parser.add_argument(
        "--key_name",
        help="Name of a key in ec2 key pair to be created. Default value is \"github-bot-key\".",
        default="github-bot-key")
    parser.add_argument(
        "--queue_name",
        help="Name of a queue to be created in SQS . Default value is \"github-bot-queue\".",
        default="github-bot-queue")
    parser.add_argument(
        "--lambda_name",
        help="Name of a Lambda function to be created. Default value is \"ggithub-bot-lambda\".",
        default="github-bot-lambda")
    parser.add_argument(
        "--role_name_lambda",
        help="Name of a role to be created for Lambda . Default value is \"github-bot-lambda-role\".",
        default="github-bot-lambda-role")
    parser.add_argument(
        "--role_name_ec2",
        help="Name of a role to be created for EC2 . Default value is \"github-bot-ec2-role\".",
        default="github-bot-ec2-role")
    parser.add_argument(
        "--instance_profile_name",
        help="Name of a instance profile to be created for EC2 . Default value is \"github-instance-profile-name\".",
        default="github-instance-profile-name")
    parser.add_argument(
        "--webhook_when_porting_pr_exists",
        help="URL for webhook when porting PR exists. Default value is \"github-instance-profile-name\".",
        default='')
    parser.add_argument(
        "--webhook_when_porting_pr_created",
        help="URL for webhook when porting PR created. Default value is \"github-instance-profile-name\".",
        default='')
    parser.add_argument(
        "--info_filename",
        help="Name of the json file with deployment information to be created."
             " Default value is \"Github-bot-deploy-info.json\".",
        default="Github-bot-deploy-info.json")
    parser.add_argument(
        '--remove_bot',
        help="Option for removing already deployed bot from AWS.", dest='remove_bot',
        action='store_true')

    args = parser.parse_args()
    if args.github_token is None:
        print('You need to specify github token in local variable GITHUB_TOKEN_FOR_BOT or with --github_token argument')
    else:
        if not args.remove_bot:
            deployment_info = {'key_name': args.key_name,
                               'queue_name': args.queue_name,
                               'lambda_name': args.lambda_name,
                               'role_name_lambda': args.role_name_lambda,
                               'role_name_ec2': args.role_name_ec2,
                               'instance_profile_name': args.instance_profile_name,
                               'git_author': args.git_author,
                               'hook_exists': args.webhook_when_porting_pr_exists,
                               'hook_created': args.webhook_when_porting_pr_created}

            deploy_bot(args.github_token, deployment_info, args.info_filename)
        else:
            remove_bot(args.info_filename)


if __name__ == "__main__":
    main()
