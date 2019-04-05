import json
import boto3
from subprocess import Popen, call
import requests
import datetime
import os
import io


def write_in_log(log_message):
    now = datetime.datetime.now()
    if not os.path.isdir('logs-github-bot/'):
        os.mkdir('logs-github-bot/')
    with open('logs-github-bot/{}.txt'.format(now.strftime('%Y-%m-%d')), 'a') as logfile:
        logfile.write('{} {}\n'.format(now.strftime('%Y-%m-%d %H:%M:%S'), log_message))


def update():
    call(['git', '-C', 'odoo-devops', 'fetch', '--all'])
    call(['git', '-C', 'odoo-devops', 'reset', '--hard', 'origin'])


def write_message(message):
    now = datetime.datetime.now()
    message_num = 1
    if not os.path.isdir('logs-github-bot/messages'):
        os.mkdir('logs-github-bot/messages')
    while os.path.isfile('logs-github-bot/messages/{}-{}.txt'.format(now.strftime('%Y-%m-%d'), message_num)):
        message_num += 1
    with io.open('logs-github-bot/messages/{}-{}.txt'.format(now.strftime('%Y-%m-%d'), message_num),
                 'w', encoding="utf-8") as file:
        file.write(message)


def main():
    write_in_log('ec2-run script is running')

    write_in_log('updating...')
    update()

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
        write_message(message.body)

        body = json.loads(message.body)

        required_fields = ['action', 'number', 'repository']

        if all(field in body for field in required_fields):
            if body['action'] == 'opened':
                Popen(['python', 'odoo-devops/tools/merge-bot/review-bot.py',
                       body['repository']['full_name'], str(body['number']), '--github_token', github_token])

                write_in_log('review-script is running for pull request {} in repository: {}'.format(body['number'],
                                                                                    body['repository']['full_name'] ))
            else:
                write_in_log('pull request is {}, not opened'.format(body['action']))

            Popen(['sudo', 'shutdown', '-c'])
            Popen(['sudo', 'shutdown', '-h', '+{}'.format(shutdown_time)])

            write_in_log('shutdown is initiated in {} minutes'.format(shutdown_time))

        else:
            absent_fields = ''
            for field in required_fields:
                if 'field' not in body:
                    absent_fields += '{}, '.format(field)
            absent_fields = absent_fields[:-2]
            write_in_log('wrong message format. Fields {} not found'.format(absent_fields))

        queue.delete_messages(Entries=[{
            'Id': message.message_id,
            'ReceiptHandle': message.receipt_handle
        }])


if __name__ == "__main__":
    main()
