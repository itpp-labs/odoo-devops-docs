import json
import os
import boto3
from subprocess import call


def main():
    queue_name = os.getenv('QUEUE_NAME')
    shutdown_time = int(os.getenv('SHUTDOWN_TIME'))
    region_name = os.getenv('REGION_NAME')
    sqs = boto3.resource('sqs', region_name=region_name)
    queue = sqs.get_queue_by_name(QueueName=queue_name)
    message = queue.receive_messages(MaxNumberOfMessages=1)
    if len(message) > 0 and shutdown_time != 0:
        call(['sudo', 'shutdown', '-c'])
        call(['sudo', 'shutdown', '-h', '+{}'.format(shutdown_time)])
    while len(message) > 0:
        body = json.loads(message[0].body)
        if body['action']:
            print('review-bot.py', body['repository']['full_name'], body['number'])
            call(['review-bot.py', body['repository']['full_name'], str(body['number'])])
        #message.delete()
        message = queue.receive_messages(MaxNumberOfMessages=1)


if __name__ == "__main__":
    main()
