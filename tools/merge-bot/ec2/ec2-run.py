"""Script for ec2 instance to run."""

import json
import boto3
from subprocess import Popen, call, check_output
import requests
import datetime
import os
import io


def write_in_log(log_message):
    """
    Writes log messages to log file.

    :param log_message:
        Text of the message.
    """

    now = datetime.datetime.now()
    if not os.path.isdir('/home/ec2-user/logs-github-bot/'):
        os.mkdir('/home/ec2-user/logs-github-bot/')
    with open('/home/ec2-user/logs-github-bot/{}.txt'.format(now.strftime('%Y-%m-%d')), 'a') as logfile:
        logfile.write('{} {}\n'.format(now.strftime('%Y-%m-%d %H:%M:%S'), log_message))


def write_message(message):
    """
    Writes message from queue to logs.

    :param message:
        Text of the message.
    """

    now = datetime.datetime.now()
    message_num = 1
    if not os.path.isdir('/home/ec2-user/logs-github-bot/messages'):
        os.mkdir('/home/ec2-user/logs-github-bot/messages')
    while os.path.isfile('/home/ec2-user/logs-github-bot/messages/{}-{}.txt'.format(now.strftime('%Y-%m-%d'),
                                                                                    message_num)):
        message_num += 1
    with io.open('/home/ec2-user/logs-github-bot/messages/{}-{}.txt'.format(now.strftime('%Y-%m-%d'), message_num),
                 'w', encoding="utf-8") as file:
        file.write(unicode(message))


def update_repository(path):
    """
    Updates repo in specified path.

    :param path:
        Path of folder where repo is located.

    """

    call(['git', '-C', path, 'fetch', '--all'])
    call(['git', '-C', path, 'reset', '--hard', 'origin'])


def update_bot():
    """
    Updates bot itself.
    """

    call(['git', '-C', 'odoo-devops', 'fetch', '--all'])
    call(['git', '-C', 'odoo-devops', 'reset', '--hard', 'origin'])


def process_message(msg_body, required_fields, github_token):
    """
    Processes message.

    :param msg_body:
        Message to process in dictionary format.
    :param required_fields:
        Fields witch must be in message body to process it.
    :return:
        If message is processed correctly returns True.
    """

    successful = False

    if all(fld in msg_body for fld in required_fields):
        full_repo_name = msg_body['repository']['full_name']
        repo_name = msg_body['repository']['name']

        repo_path = '/home/ec2-user/repositories/{}'.format(repo_name)
        action = msg_body['action']
        merged = msg_body['pull_request']['merged']
        base_branch = msg_body['pull_request']['base']['ref']

        if action == 'closed' and merged and base_branch in ['10.0', '11.0']:
            next_branch = str(int(base_branch.split('.')[0]) + 1) + '.0'

            if next_branch in ['11.0', '12.0']:

                write_in_log('forking repo: {}'.format(full_repo_name))

                Popen(['python', '/home/ec2-user/odoo-devops/tools/merge-bot/scripts/fork.py',
                       full_repo_name, '--github_token', github_token]).wait()
                write_in_log('fork complete')

                if os.path.isdir(repo_path):
                    write_in_log('updating repo in {}'.format(repo_path))
                    update_repository(repo_path)
                    write_in_log('update complete')

                else:
                    write_in_log('cloning fork repo in {}'.format(repo_path))
                    Popen(['python', '/home/ec2-user/odoo-devops/tools/merge-bot/scripts/clone_fork.py',
                           repo_name, repo_path, '--github_token', github_token]).wait()
                    write_in_log('clone complete')

                write_in_log('merging repo: {}'.format(full_repo_name))
                os.chdir(repo_path)

                Popen(['python', '/home/ec2-user/odoo-devops/tools/merge-bot/scripts/merge.py',
                       base_branch, next_branch, '--auto_push']).wait()
                write_in_log('merge in branch {} complete'.format(next_branch))

                merge_branch = check_output(['git', 'rev-parse', '--abbrev-ref', 'HEAD']).decode()[:-1]
                fork_user =\
                    check_output(['git', 'remote', 'get-url', 'origin']).decode().split('/')[-2]

                write_in_log('making pull-request in {} {} from {} {}'.format(full_repo_name, next_branch,
                                                                              fork_user, merge_branch))
                Popen(['python', '/home/ec2-user/odoo-devops/tools/merge-bot/scripts/pull-request.py',
                       full_repo_name, next_branch, fork_user, merge_branch, '--github_token', github_token]).wait()

                write_in_log('pull-request complete'.format(next_branch))

            else:
                write_in_log('merge in branch "{}" is not supported'.format(next_branch))

        else:
            write_in_log('action is {}, pull request not merged'.format(action))

        successful = True

    else:
        absent_fields = ''
        for field in required_fields:
            if 'field' not in msg_body:
                absent_fields += '{}, '.format(field)
        absent_fields = absent_fields[:-2]
        write_in_log('wrong message format. Fields {} not found'.format(absent_fields))

    return successful


def main():
    write_in_log('ec2-run script is running')

    write_in_log('updating bot...')
    update_bot()

    region_name = requests.get('http://169.254.169.254/latest/meta-data/placement/availability-zone').text[:-1]
    ssm_client = boto3.client('ssm', region_name=region_name)

    queue_name = ssm_client.get_parameter(Name='QUEUE_NAME', WithDecryption=True)['Parameter']['Value']
    shutdown_time = ssm_client.get_parameter(Name='SHUTDOWN_TIME', WithDecryption=True)['Parameter']['Value']
    github_token = ssm_client.get_parameter(Name='GITHUB_TOKEN_FOR_BOT', WithDecryption=True)['Parameter']['Value']

    sqs = boto3.resource('sqs', region_name=region_name)
    queue = sqs.get_queue_by_name(QueueName=queue_name)

    write_in_log('Region name: {}; Queue name: {}; Shutdown time: {}'.format(region_name, queue_name, shutdown_time))

    messages = []
    response = queue.receive_messages(MaxNumberOfMessages=10)
    while len(response) > 0:
        messages.extend(response)
        response = queue.receive_messages(MaxNumberOfMessages=10)

    write_in_log('{} messages received from SQS'.format(len(messages)))

    for message in messages:
        msg_body = json.loads(message.body)
        required_fields = ['action', 'number', 'repository']

        write_message(message.body)
        successful = process_message(msg_body, required_fields, github_token)

        queue.delete_messages(Entries=[{
            'Id': message.message_id,
            'ReceiptHandle': message.receipt_handle
        }])

    if len(messages) == 0:

        write_in_log('shutdown is in schedule')
    else:

        Popen(['sudo', 'shutdown', '-c'])
        write_in_log('shutdown is initiated in {} minutes'.format(shutdown_time))

    Popen(['sudo', 'shutdown', '-h', '+{}'.format(shutdown_time)])


if __name__ == "__main__":
    main()
