# Copyright 2020 Ivan Yelizariev <https://it-projects.info/team/yelizariev>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import json
import logging
import os
import re
from datetime import datetime
# https://github.com/python-telegram-bot/python-telegram-bot
from telegram import Update, Bot, ReplyKeyboardMarkup


logger = logging.getLogger()
LOG_LEVEL = os.getenv("LOG_LEVEL")
if LOG_LEVEL:
    level = getattr(logging, LOG_LEVEL)
    logging.basicConfig(format='%(name)s [%(levelname)s]: %(message)s', level=level)

bot = Bot(token=os.getenv('TELEGRAM_TOKEN'))


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
    if not update.message:
        return

    if message.text == "/start":
        bot.sendMessage(message.chat.id, "This is a private bot to start/stop AWS EC2 instances. Check documentation at https://itpp.dev/ops/remote-dev/aws/index.html")
        return

    # check that we know the user
    server = os.getenv("USER_%s_SERVER" % user_id)
    user_code = os.getenv("USER_%s_CODE" % user_id)
    if not (server and user_code):
        bot.sendMessage(message.chat.id, "Access denied!")
        return

    # do what the user asks
    if message.text == "/up":
        start_server(server, user_code)
    elif message.text == "/shutdown":
        confirm_buttons = ReplyKeyboardMarkup([["Shutdown", "Cancel"]])
        bot.sendMessage(message.chat.id, "Are you sure?", reply_markup=confirm_buttons)
    elif str(message.text).lower() == "shutdown":
        stop_server(server)

def handle_cron(cloudwatch_time):
    dt = datetime.strptime(cloudwatch_time, TIME_FORMAT)
    unixtime = (dt - datetime(1970, 1, 1)).total_seconds()
    # TODO

def start_server(server, user_code):
    bot.sendMessage(message.chat.id, "Server is starting... TODO")

def stop_server(server):
    bot.sendMessage(message.chat.id, "Server is stopping... TODO")
