import json
import logging
import os
import re
from botocore.vendored import requests
from botocore.vendored.requests.packages import urllib3

GREEN = 'green'
RED = 'red'
NOT_FINISH = 'not_finish'
LOG_LEVEL = os.environ.get('LOG_LEVEL')
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
USERNAMES = os.environ.get('USERNAMES')
MSG_RQST_MERGE = os.environ.get('MSG_RQST_MERGE', 'I approve to merge it now')
IFTTT_HOOK_RED_PR = os.environ.get('IFTTT_HOOK_RED_PR')
IFTTT_HOOK_GREEN_PR = os.environ.get('IFTTT_HOOK_GREEN_PR')
IFTTT_HOOK_NOT_FINISHED_PR = os.environ.get('IFTTT_HOOK_NOT_FINISHED_PR')

logger = logging.getLogger()
if LOG_LEVEL:
    logger.setLevel(getattr(logging, LOG_LEVEL))


def lambda_handler(event, context):
    logger.debug("Event: \n%s", json.dumps(event))
    payload = json.loads(event["body"])
    logger.debug("Payload: \n%s", json.dumps(payload))
    comment = payload.get('comment')
    if not comment:
        return
    comment = comment['body'].strip()
    if comment == MSG_RQST_MERGE:
        owner = payload.get('repository')['owner']['login']
        repo = payload.get('repository')['name']
        pull_request = payload.get('issue')['html_url']
        pull = re.search("/pull(/[0-9]+)", pull_request).group(1)
        pull_number = re.search("/pull/([0-9]+)", pull_request).group(1)
        pulls_url = payload['repository']['pulls_url']
        # pull_info: https://developer.github.com/v3/pulls/#get-a-single-pull-request
        pull_info = get_pull_info(pulls_url, pull)
        pull_request_state = pull_info['state']

        if pull_request_state in ('closed', 'merged'):
            logger.debug('State of pull request: %s ', pull_request_state)
            return

        branch_origin = pull_info['head']['ref']
        username = payload.get('comment')['user']['login']
        headers = {
            'Authorization': 'token %s' % GITHUB_TOKEN,
            'Content-Type': 'application/json',
            'User-Agent': 'aws lambda handler'
        }
        if username in USERNAMES.split(","):
            # commit SHA-1 hash of head branch repo
            sha_head = pull_info['head']['sha']
            # name of head user
            owner_head = pull_info['head']['user']['login']
            # name of base user
            owner_base = pull_info['base']['user']['login']
            # name of head repo
            repo_head = pull_info['head']['repo']['name']
            state = get_status_pr(owner_base, repo_head, sha_head)['state']
            check_runs = get_status_check_run(owner_head, repo_head, branch_origin).get('check_runs')
            # Merge a pull request (Merge Button): https://developer.github.com/v3/pulls/
            merge = make_merge_pr(owner, repo, pull_number, headers)
            if merge == 200:
                # Comments: https://developer.github.com/v3/issues/comments/
                approve_comment = 'Approved by @%s' % username
                make_issue_comment(owner, repo, pull_number, headers, approve_comment)
                res = status_result(check_runs, state, pull_number)
                ifttt_handler(res, pull_info)
            elif merge == 404:
                approve_comment = 'Sorry @%s, I don\'t have access rights to push to this repository' % username
                make_issue_comment(owner, repo, pull_number, headers, approve_comment)
            else:
                approve_comment = '@%s. Merge is not successful. See logs' % username
                make_issue_comment(owner, repo, pull_number, headers, approve_comment)
        else:
            approve_comment = 'Sorry @%s, but you don\'t have access to merge it' % username
            make_issue_comment(owner, repo, pull_number, headers, approve_comment)
    else:
        logger.debug('Comment: %s ', comment)


def get_status_check_run(owner_head, repo_head, branch_origin):
    # GET /repos/:owner/:repo/commits/:ref/check-runs
    url = 'https://api.github.com/repos/%s/%s/commits/%s/check-runs' % (owner_head, repo_head, branch_origin)
    http = urllib3.PoolManager()
    res = http.request('GET', url, headers={
        # 'Content-Type': 'application/vnd.github.v3.raw+json',
        'User-Agent': 'aws lambda handler',
        'Accept': 'application/vnd.github.antiope-preview+json',
        'Authorization': 'token %s' % GITHUB_TOKEN,
    })
    res = json.loads(res.data)
    logger.debug("Status of Check runs: \n%s", json.dumps(res))
    return res


def get_status_pr(owner_base, repo_head, sha_head):
    # GET /repos/:owner/:repo/commits/:ref/status
    url = 'https://api.github.com/repos/%s/%s/commits/%s/status' % (owner_base, repo_head, sha_head)
    http = urllib3.PoolManager()
    res = http.request('GET', url, headers={
        # 'Content-Type': 'application/vnd.github.v3.raw+json',
        'User-Agent': 'aws lambda handler',
        'Accept': 'application/vnd.github.antiope-preview+json',
        'Authorization': 'token %s' % GITHUB_TOKEN,
    })
    res = json.loads(res.data)
    logger.debug("Status pull request: \n%s", json.dumps(res))
    return res


def status_result(check_runs, state, pull_number):
    statuses_check_run = []
    conclusions_check_run = []
    for check_run in check_runs:
        pull_requests = check_run.get('pull_requests')
        for pull_request in pull_requests:
            pull_number_by_check_run = pull_request.get('number')
            if str(pull_number_by_check_run) == pull_number:
                statuses_check_run.append(check_run.get('status'))
                conclusions_check_run.append(check_run.get('conclusion'))
    logger.debug('List of conclusions check run: %s ', conclusions_check_run)
    logger.debug('List of statuses check run: %s ', statuses_check_run)
    res = ''
    if all(elem in statuses_check_run for elem in ['completed']) and state != 'pending':
        result = any(elem in conclusions_check_run for elem in ['failure', 'neutral', 'cancelled', 'timed_out', 'action_required'])
        if result or state == 'failure':
            res = RED
        elif state == 'success':
            res = GREEN
    elif any(elem in statuses_check_run for elem in ['queued', 'in_progress']) or state == 'pending':
        res = NOT_FINISH
    return res


def ifttt_handler(res, pull_info):
    login = pull_info['user']['login']
    pr_html_url = pull_info.get('html_url')
    logger.debug('Result status of pull request: %s ', res)
    if res == RED:
        msg_for_red_tests = 'This PR was merge with a red tests'
        notify_ifttt(
            IFTTT_HOOK_RED_PR,
            value1=login,
            value2=pr_html_url,
            value3=msg_for_red_tests
        )
        return
    elif res == GREEN:
        # successful
        msg_for_green_tests = 'This PR was merge with a green tests'
        notify_ifttt(
            IFTTT_HOOK_GREEN_PR,
            value1=login,
            value2=pr_html_url,
            value3=msg_for_green_tests
        )
        return
    else:
        # not finished yet
        msg_not_finish = 'This PR was merge without waiting for tests'
        logger.debug('Msg_not_finish: %s ', msg_not_finish)
        notify_ifttt(
            IFTTT_HOOK_NOT_FINISHED_PR,
            value1=login,
            value2=pr_html_url,
            value3=msg_not_finish
        )
        return


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


def make_merge_pr(owner, repo, pull_number, headers):
    # PUT /repos/:owner/:repo/pulls/:pull_number/merge
    url = 'https://api.github.com/repos/%s/%s/pulls/%s/merge' % (owner, repo, pull_number)
    response = requests.request("PUT", url, headers=headers)
    if response.status_code == 200:
        logger.debug('Pull Request %s successfully merged', pull_number)
        return response.status_code
    else:
        logger.debug('Response: "%s"', response.content)
        return response.status_code


def make_issue_comment(owner, repo, pull_number, headers, approve_comment=None):
    # POST /repos/:owner/:repo/issues/:issue_number/comments
    url = 'https://api.github.com/repos/%s/%s/issues/%s/comments' % (owner, repo, pull_number)
    body = {'body': approve_comment}
    comment = json.dumps(body)
    response = requests.request("POST", url, data=comment, headers=headers)
    if response.status_code == 201:
        logger.debug('Successfully created Comment "%s"', comment)
    else:
        logger.debug('Could not create Comment "%s"', comment)
        logger.debug('Response: "%s"', response.content)
