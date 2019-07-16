import json
import logging
import os
import re
from botocore.vendored import requests
from botocore.vendored.requests.packages import urllib3

LOG_LEVEL = os.environ.get('LOG_LEVEL')
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
USERNAMES = os.environ.get('USERNAMES')
MSG_RQST_MERGE = os.environ.get('MSG_RQST_MERGE', 'I approve to merge it now')

logger = logging.getLogger()
if LOG_LEVEL:
    logger.setLevel(getattr(logging, LOG_LEVEL))


def lambda_handler(event, context):
    logger.debug("Event: \n%s", json.dumps(event))
    payload = json.loads(event["body"])
    logger.debug("Payload: \n%s", json.dumps(payload))
    comment = payload.get('comment')['body']
    if comment.strip() == MSG_RQST_MERGE:
        owner = payload.get('repository')['owner']['login']
        repo = payload.get('repository')['name']
        pull_request = payload.get('issue')['html_url']
        pull = re.search("/pull(/[0-9]+)", pull_request).group(1)
        pull_number = re.search("/pull/([0-9]+)", pull_request).group(1)
        pulls_url = payload['repository']['pulls_url']
        # pull_info: https://developer.github.com/v3/pulls/#get-a-single-pull-request
        pull_info = get_pull_info(pulls_url, pull)
        branch_origin = pull_info['head']['ref']
        branch_upstream = pull_info['base']['ref']
        username = payload.get('comment')['user']['login']
        headers = {
            'Authorization': 'token %s' % GITHUB_TOKEN,
            'Content-Type': 'application/json',
            'User-Agent': 'aws lambda handler'
        }
        if username in USERNAMES.split(","):
            # Merging: https://developer.github.com/v3/repos/merging
            make_merge_pr(owner, repo, pull_number, headers)
            # Comments: https://developer.github.com/v3/issues/comments/
            approve_comment = 'Approved by @%s' % username
            make_issue_comment(owner, repo, pull_number, headers, approve_comment)
        else:
            approve_comment = 'Sorry @%s, but you don\'t have access to merge it' % username
            make_issue_comment(owner, repo, pull_number, headers, approve_comment)
    else:
        logger.debug('Comment: %s ', comment)
    if not comment:
        return


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
        return True
    else:
        logger.debug('Response: "%s"', response.content)
        return False


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
