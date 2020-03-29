# Copyright 2020 Ivan Yelizariev <https://it-projects.info/team/yelizariev>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import json
import logging
import os
import re


logger = logging.getLogger()
if LOG_LEVEL:
    logger.setLevel(getattr(logging, LOG_LEVEL))


def lambda_handler(event, context):
    logger.debug("Event: \n%s", json.dumps(event))
    payload = json.loads(event["body"])
    logger.debug("Payload: \n%s", json.dumps(payload))
