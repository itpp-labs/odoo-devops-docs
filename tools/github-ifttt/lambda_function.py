import json
import logging
import os
import re
from botocore.vendored.requests.packages import urllib3

LOG_LEVEL = os.environ.get('LOG_LEVEL')
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
IFTTT_HOOK_RED_PR = os.environ.get('IFTTT_HOOK_RED_PR')
IFTTT_HOOK_RED_BRANCH = os.environ.get('IFTTT_HOOK_RED_BRANCH')
IFTTT_HOOK_GREEN_PR = os.environ.get('IFTTT_HOOK_GREEN_PR')

logger = logging.getLogger()
if LOG_LEVEL:
    logger.setLevel(getattr(logging, LOG_LEVEL))


def lambda_handler(event, context):
    logger.debug("Event: \n%s", json.dumps(event))
    payload = json.loads(event["body"])
    logger.debug("Payload: \n%s", json.dumps(payload))
    result = handle_payload(payload)

    if not result:
        logger.info("Nothing to do")

    # TODO implement
    return {
        'statusCode': 200,
        'body': json.dumps('Done!' if result else "Thanks, but nothing to do here")
    }


def handle_payload(payload):
    # payload: https://developer.github.com/v3/activity/events/types/#webhook-payload-example
    # check_run: https://developer.github.com/v3/checks/runs/#parameters
    check_run = payload.get('check_run')
    if not check_run:
        return

    conclusion = check_run.get('conclusion')
    logger.debug('conclusion: %s', conclusion)
    if not conclusion:
        # not finished yet
        return

    if conclusion in ['neutral', 'cancelled']:
        # ok
        return

    # TODO make more strong check for travis
    if check_run['name'] == "Travis CI - Pull Request":
        return handle_payload_pr(payload, check_run, conclusion)
    elif check_run['name'] == "Travis CI - Branch":
        return handle_payload_branch(payload, check_run, conclusion)
    else:
        logger.debug('Unknown check name: %s', check_run['name'])
        return


def handle_payload_pr(payload, check_run, conclusion):
    output_text = check_run['output']['text']
    pull = re.search("/pull(/[0-9]+)", output_text).group(1)
    pulls_url = payload['repository']['pulls_url']
    # pull_info: https://developer.github.com/v3/pulls/#get-a-single-pull-request
    pull_info = get_pull_info(pulls_url, pull)
    login = pull_info['user']['login']
    check_run_html_url = check_run.get('html_url')
    pr_html_url = pull_info.get('html_url')

    if conclusion == 'success':
        notify_ifttt(
            IFTTT_HOOK_GREEN_PR,
            value1=login,
            value2=pr_html_url,
            value3=check_run_html_url
        )
    else:
        # failed
        notify_ifttt(
            IFTTT_HOOK_RED_PR,
            value1=login,
            value2=pr_html_url,
            value3=check_run_html_url
        )
    return True


def handle_payload_branch(payload, check_run, conclusion):
    login = payload.get('sender')['login']
    check_run_html_url = check_run.get('html_url')
    search_repo_result = re.search(r'\/.*\/(.*)\/runs', check_run_html_url)
    repo = search_repo_result.group(1)
    check_run_head_branch = check_run.get('check_suite').get('head_branch')
    check_run_details_url = check_run.get('details_url')

    if conclusion in ('failed', 'failure'):
        notify_ifttt(
            IFTTT_HOOK_RED_BRANCH,
            value1=check_run_head_branch,
            value2=repo,
            value3=check_run_details_url,
        )
    return True


def notify_ifttt(hook, **data):
    logger.debug("notify_ifttt: %s", data)
    http = urllib3.PoolManager()
    res = http.request(
        'POST', hook,
        body=json.dumps(data),
        headers={
            'Content-Type': 'application/json',
            'User-Agent': 'aws lambda handler',
        })
    return res


def get_pull_info(pulls_url, pull):
    url = pulls_url.replace('{/number}', pull)

    http = urllib3.PoolManager()
    res = http.request('GET', url, headers={
        'User-Agent': 'aws lambda handler',
        'Authorization': 'token %s' % GITHUB_TOKEN,
    })
    res = json.loads(res.data)
    logger.debug("Pull info via %s: \n%s", url, json.dumps(res))
    return res