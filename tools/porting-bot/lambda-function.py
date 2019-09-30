import os
from botocore.vendored import requests
import boto3


def handler(event, context):
    make_review(event)
    return {
        'statusCode': 200
    }


def get_file(url):
    return requests.get(url).text


def make_review(event):
    instance_id = os.getenv("INSTANCE_ID")
    queue_name = os.getenv("QUEUE_NAME")
    sqs = boto3.resource('sqs')
    queue = sqs.get_queue_by_name(QueueName=queue_name)
    queue.send_message(MessageBody=event['body'])

    ec2 = boto3.resource('ec2')

    instance = ec2.Instance(instance_id)
    while instance.state['Name'] not in ['running', 'pending']:
        print('Instance {} is {}'.format(instance_id, instance.state['Name']))
        if instance.state['Name'] == 'stopped':
            instance.start()
        elif instance.state['Name'] == 'stopping':
            instance.wait_until_stopped()
        instance = ec2.Instance(instance_id)

    print('Instance {} is {}'.format(instance_id, instance.state['Name']))
