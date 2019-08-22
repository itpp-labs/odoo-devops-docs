# Copyright 2019 Ivan Yelizariev <https://it-projects.info/team/yelizariev>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import json
import logging
import os
import re
from botocore.vendored import requests
from botocore.vendored.requests.packages import urllib3


RED_STATUSES = ['failure', 'neutral', 'cancelled', 'timed_out', 'action_required', 'error']
NOT_FINISHED_STATUSES = ['queued', 'in_progress', 'pending']
GREEN = 'green'
RED = 'red'
NOT_FINISHED = 'not_finished'
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

        username = payload.get('comment')['user']['login']
        headers = {
            'Authorization': 'token %s' % GITHUB_TOKEN,
            'Content-Type': 'application/json',
            'User-Agent': 'aws lambda handler'
        }
        if username in USERNAMES.split(","):
            sha_head = pull_info['head']['sha']
            owner_base = pull_info['base']['user']['login']
            repo_head = pull_info['head']['repo']['name']
            status_state = [get_status_pr(owner_base, repo_head, sha_head).get('state')]
            logger.debug('Status of state: %s ', status_state)
            check_runs = get_status_check_run(owner_base, repo_head, sha_head).get('check_runs')
            # Merge a pull request (Merge Button): https://developer.github.com/v3/pulls/
            merge = make_merge_pr(owner, repo, pull_number, headers)
            if merge == 200:
                # Comments: https://developer.github.com/v3/issues/comments/
                approve_comment = 'Approved by @%s' % username
                make_issue_comment(owner, repo, pull_number, headers, approve_comment)
                res = status_result(check_runs, status_state)
                ifttt_handler(res, pull_info, username)
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


def get_status_check_run(owner_base, repo_head, sha_head):
    # GET /repos/:owner/:repo/commits/:ref/check-runs
    url = 'https://api.github.com/repos/%s/%s/commits/%s/check-runs' % (owner_base, repo_head, sha_head)
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


def status_result(check_runs, status_state):
    # get list of statuses check run. May be queued, in_progress or completed. And
    # get list of conclusions check run. May be success, failure, neutral, cancelled, timed_out, or action_required if status is completed
    statuses_check_run = []
    conclusions_check_run = []
    for check_run in check_runs:
        statuses_check_run.append(check_run.get('status'))
        conclusions_check_run.append(check_run.get('conclusion'))
    logger.debug('List of statuses check run: %s ', statuses_check_run)
    logger.debug('List of conclusions check run: %s ', conclusions_check_run)
    states = statuses_check_run + conclusions_check_run + status_state
    logger.debug('States: %s ', states)
    if any(elem in states for elem in RED_STATUSES):
        return RED
    elif any(elem in states for elem in NOT_FINISHED_STATUSES):
        return NOT_FINISHED
    else:
        return GREEN


def ifttt_handler(res, pull_info, username):
    pr_html_url = pull_info.get('html_url')
    author_pr = pull_info['head']['user']['login']
    values = {'value1': username,
              'value2': author_pr,
              'value3': pr_html_url}
    if res == RED:
        notify_ifttt(IFTTT_HOOK_RED_PR, **values)
        return
    elif res == GREEN:
        # successful
        notify_ifttt(IFTTT_HOOK_GREEN_PR, **values)
        return
    else:
        # not finished yet
        notify_ifttt(IFTTT_HOOK_NOT_FINISHED_PR, **values)
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
