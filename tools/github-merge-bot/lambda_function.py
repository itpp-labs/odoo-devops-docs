import json
import logging
import os
import re
from botocore.vendored import requests
from botocore.vendored.requests.packages import urllib3

LOG_LEVEL = os.environ.get('LOG_LEVEL')
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
USERNAMES = os.environ.get('USERNAMES')

logger = logging.getLogger()
if LOG_LEVEL:
    logger.setLevel(getattr(logging, LOG_LEVEL))


def lambda_handler(event):
    logger.debug("Event: \n%s", json.dumps(event))
    payload = json.loads(event["body"])
    logger.debug("Payload: \n%s", json.dumps(payload))
    comment = payload.get('comment')['body']
    username = payload.get('issue')['user']['login']
    if comment.strip() == 'I approve to merge it now' and username in USERNAMES.split(","):
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
        headers = {
            'Authorization': 'token %s' % GITHUB_TOKEN,
            'Content-Type': 'application/json',
            'User-Agent': 'aws lambda handler'
        }
        # Merging: https://developer.github.com/v3/repos/merging
        make_merge(owner, repo, branch_upstream, branch_origin, headers)
        # Comments: https://developer.github.com/v3/issues/comments/
        approve_comment = 'Approved by @%s' % username
        make_issue_comment(owner, repo, pull_number, headers, approve_comment)
    else:
        logger.debug('Comment: %s ' % comment)
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


def make_merge(owner, repo, branch_upstream, branch_origin, headers):
    # POST /repos/:owner/:repo/merges
    url = 'https://api.github.com/repos/%s/%s/merges' % (owner, repo)
    body = {
        'base': branch_upstream,
        'head': branch_origin
    }
    merge = json.dumps(body)
    response = requests.request("POST", url, data=merge, headers=headers)
    if response.status_code == 201:
        logger.debug('Successfully created Merge "%s"' % merge)
    else:
        logger.debug('Could not create Merge "%s"' % merge)
        logger.debug('Response:', response.content)


def make_issue_comment(owner, repo, pull_number, headers, approve_comment=None):
    # POST /repos/:owner/:repo/issues/:issue_number/comments
    url = 'https://api.github.com/repos/%s/%s/issues/%s/comments' % (owner, repo, pull_number)
    body = {'body': approve_comment}
    comment = json.dumps(body)
    response = requests.request("POST", url, data=comment, headers=headers)
    if response.status_code == 201:
        logger.debug('Successfully created Comment "%s"' % comment)
    else:
        logger.debug('Could not create Comment "%s"' % comment)
        logger.debug('Response:', response.content)
