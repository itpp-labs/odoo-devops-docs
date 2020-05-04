# Copyright 2020 Ivan Yelizariev <https://it-projects.info/team/yelizariev>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import json
import logging
import os
import re
import boto3
from datetime import datetime
# https://github.com/python-telegram-bot/python-telegram-bot
from telegram import Update, Bot, ReplyKeyboardMarkup, ReplyKeyboardRemove


logger = logging.getLogger()
LOG_LEVEL = os.getenv("LOG_LEVEL")
DEBUG = LOG_LEVEL == "DEBUG"
if LOG_LEVEL:
    level = getattr(logging, LOG_LEVEL)
    logging.basicConfig(format='%(name)s [%(levelname)s]: %(message)s', level=level)

bot = Bot(token=os.getenv('TELEGRAM_TOKEN'))
ec2 = boto3.resource('ec2')


def lambda_handler(event, context):
    # read event
    logger.debug("Event: \n%s", json.dumps(event))

    telegram_payload = None
    cloudwatch_time = None
    if event.get("source") == "aws.events":
        cloudwatch_time = event.get('time')
    else:
        telegram_payload = json.loads(event.get("body", '{}'))
        logger.debug("Telegram event: \n%s", telegram_payload)

    # handle event
    try:
        if telegram_payload:
            handle_telegram(telegram_payload)
        elif cloudwatch_time:
            handle_cron(cloudwatch_time)
    except:
        logger.error("Error on handling event", exc_info=True)

    # return ok to telegram server
    return {"statusCode": 200, "headers": {}, "body": ""}

def handle_telegram(telegram_payload):
    update = Update.de_json(telegram_payload, bot)
    message = update.message
    if not message:
        return

    if message.text == "/start":
        bot.sendMessage(message.chat.id, "This is a private bot to start/stop AWS EC2 instances. Check out the documentation:\nhttps://itpp.dev/ops/remote-dev/aws/index.html")
        return

    # check that we know the user
    user_id = message.from_user.id
    instance_id = os.getenv("USER_%s_INSTANCE" % user_id)
    user_code = os.getenv("USER_%s_CODE" % user_id)
    if not (instance_id and user_code):
        bot.sendMessage(message.chat.id, "Access denied!")
        return

    instance = ec2.Instance(instance_id)
    # do what the user asks
    if message.text == "/up":
        start_instance(message, instance, user_code)
    if message.text == "/status":
        send_status(message, instance, user_code)
    elif message.text == "/shutdown":
        confirm_buttons = ReplyKeyboardMarkup([["Shutdown", "Cancel"]])
        bot.sendMessage(message.chat.id, "Are you sure?", reply_markup=confirm_buttons)
    elif str(message.text).lower() == "shutdown":
        stop_instance(message, instance)
    elif str(message.text).lower() == "cancel":
        bot.sendMessage(message.chat.id, "Canceled", reply_markup=ReplyKeyboardRemove())

def handle_cron(cloudwatch_time):
    dt = datetime.strptime(cloudwatch_time, TIME_FORMAT)
    unixtime = (dt - datetime(1970, 1, 1)).total_seconds()
    # TODO

def start_instance(message, instance, user_code):
    bot.sendMessage(message.chat.id, "Instance is starting...")
    response = instance.start()
    if DEBUG:
        bot.sendMessage(message.chat.id, "Response from AWS: %s" % json.dumps(response))
    instance.wait_until_running()
    send_status(message, instance, user_code)

def stop_instance(message, instance):
    bot.sendMessage(message.chat.id, "Instance is stopping...", reply_markup=ReplyKeyboardRemove())
    response = instance.stop()
    if DEBUG:
        bot.sendMessage(message.chat.id, "Response from AWS: %s" % json.dumps(response))
    instance.wait_until_stopped()
    send_status(message, instance)

def send_status(message, instance, user_code=None):
    msg = ["Status: %s" % instance.state['Name']]
    if instance.public_dns_name:
        msg.append("Public DNS: %s " % instance.public_dns_name)

    # For byte codes meaning see the docs
    # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#EC2.Instance.state
    state_code = instance.state['Code']
    if state_code & 255 == 16:
        # running
        msg.append("")
        msg.append("To stop instance click /shutdown or schedule message \"Shutdown\"")

    bot.sendMessage(message.chat.id, '\n'.join(msg))
