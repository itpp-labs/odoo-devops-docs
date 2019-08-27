#!/usr/bin/python
import ast
import os
import json
import logging
import re
from botocore.vendored import requests
from github import Github
from text_tree import draw_tree, parser
from botocore.vendored.requests.packages import urllib3

LOG_LEVEL = os.environ.get('LOG_LEVEL')
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
LINK_TO_READ_DOCS = '> sent by [:v: Review Bot](https://odoo-devops.readthedocs.io/en/latest/git/github-review-bot.html)'

logger = logging.getLogger()
if LOG_LEVEL:
    logger.setLevel(getattr(logging, LOG_LEVEL))


def lambda_handler(event, context):
    logger.debug("Event: \n%s", json.dumps(event))
    payload = json.loads(event["body"])
    logger.debug("Payload: \n%s", json.dumps(payload))
    pull_request = payload.get('pull_request')['html_url']
    pull_number = re.search("/pull/([0-9]+)", pull_request).group(1)
    full_name = payload['repository']['full_name']
    full_name_head_repo = payload['pull_request']['head']['repo']['full_name']
    branch_head_repo = payload['pull_request']['head']['sha']
    state_pr = payload.get('pull_request')['state']
    if state_pr != 'closed':
        main(GITHUB_TOKEN, full_name, pull_number, full_name_head_repo, branch_head_repo)


def main(GITHUB_TOKEN, full_name, pull_number, full_name_head_repo, branch_head_repo):
    if GITHUB_TOKEN:
        github = Github(GITHUB_TOKEN)
    else:
        print('Please specify github login/password or token')
        exit()

    repo = github.get_repo(full_name)
    pr = repo.get_pull(int(pull_number))
    review_comments = []
    paths_inst_mod = []
    paths_non_inst_mod = []
    list_update_files_pr = pr.get_files()
    for pr_file in list_update_files_pr:
        module_name = pr_file.filename.split('/')[0]
        path_to_update_file = pr_file.filename
        installable = False
        if '/' in path_to_update_file:
            path_to_manifest = 'https://github.com/%s/raw/%s/%s/__manifest__.py' % (
            full_name_head_repo, str(branch_head_repo), module_name)
            path_to_openerp = 'https://github.com/%s/raw/%s/%s/__openerp__.py' % (
            full_name_head_repo, str(branch_head_repo), module_name)
            html = requests.get(path_to_manifest, headers={'Authorization': 'token %s' % GITHUB_TOKEN})
            if html.status_code != 200:
                html = requests.get(path_to_openerp, headers={'Authorization': 'token %s' % GITHUB_TOKEN})
            html = html.text
            installable = ast.literal_eval(html).get('installable')
        if installable or '/' not in path_to_update_file:
            paths_inst_mod.append(path_to_update_file)
        else:
            paths_non_inst_mod.append(path_to_update_file)
            
    logger.debug("Paths of update files in installable modules: \n%s", paths_inst_mod)
    logger.debug("Paths of update files in non-installable modules: \n%s", paths_non_inst_mod)
    tree_inst = create_tree(paths_inst_mod)
    tree_non_inst = None
    if paths_non_inst_mod != []:
        tree_non_inst = create_tree(paths_non_inst_mod)
    installable_modules = set([module.split('/')[0] for module in paths_inst_mod if '/' in module])
    non_installable_modules = set([module.split('/')[0] for module in paths_non_inst_mod])
    for pr_file in list_update_files_pr:
        path_to_pr_file = pr_file.filename
        if 'changelog.rst' in path_to_pr_file and path_to_pr_file.split('/')[0] in installable_modules:
            comment_line = 0
            change_started = False
            for line in pr_file.patch.split('\n')[1:]:
                if change_started:
                    if not line.startswith('+'):
                        break
                else:
                    if line.startswith('+'):
                        change_started = True
                comment_line += 1
            review_comments.append({'path': path_to_pr_file,
                                    'position': comment_line,
                                    'body': 'Has to be tested'})
    blank_block = "```\n```"
    quantity_inst_mod = len(installable_modules)
    quantity_non_inst_mod = len(non_installable_modules)
    review_body = "{}\n" \
                  "{}\n\n" \
                  "{}\n" \
                  "{}\n\n".format(
        '%s' % 'Installable modules remain unchanged.' if len(
            installable_modules) == 0 else '**{} installable** module{} updated:'.format(
            quantity_inst_mod, ' is' if quantity_inst_mod == 1 else 's are'),
        '%s' % (tree_inst if tree_inst else blank_block),
        '%s' % 'Not installable modules remain unchanged.' if len(
            non_installable_modules) == 0 else '**{} not installable** modules {} updated:'.format(
            quantity_non_inst_mod, ' is' if quantity_non_inst_mod == 1 else 's are'),
        '%s' % (tree_non_inst if tree_non_inst else blank_block))

    reviews = pr.get_reviews()
    id_review = None
    for review in reviews:
        body_review = review.body
        # If this link is not found, then this is not the same pull request review
        if not LINK_TO_READ_DOCS in body_review:
            continue
        id_review = review.id
        break
    if id_review:
        # Update a pull request review
        # Look: https://developer.github.com/v3/pulls/reviews/#update-a-pull-request-review
        update_review(GITHUB_TOKEN, full_name, pull_number, id_review, review_body)
    else:
        # Create a pull request review
        # Look: https://pygithub.readthedocs.io/en/latest/github_objects/PullRequest.html#github.PullRequest.PullRequest.create_review
        pr_commits = pr.get_commits()
        if not review_comments:
            review_body += 'No new features in *doc/changelog.rst* files of installable modules\n\n'
        review_body += '%s' % LINK_TO_READ_DOCS
        pr.create_review(commit=pr_commits[pr_commits.totalCount - 1],
                         body=review_body
                         , event='COMMENT', comments=review_comments)


def create_tree(paths):
    text = path_to_text(paths)
    # https://stackoverflow.com/questions/32151776/visualize-tree-in-bash-like-the-output-of-unix-tree
    tree = draw_tree(parser(text))
    return tree


def update_review(GITHUB_TOKEN, full_name, pull_number, id_review, review_body):
    # PUT /repos/:owner/:repo/pulls/:pull_number/reviews/:review_id
    url = 'https://api.github.com/repos/%s/pulls/%s/reviews/%s' % (full_name, pull_number, id_review)
    http = urllib3.PoolManager()
    body = {'body': review_body}
    res = http.request('PUT', url, headers={
        'Content-Type': 'application/vnd.github.v3.raw+json',
        'User-Agent': 'aws lambda handler',
        'Authorization': 'token %s' % GITHUB_TOKEN,
    }, body=json.dumps(body))
    res = json.loads(res.data)
    logger.debug("Update review pull request: \n%s", json.dumps(res))
    return res


def paths_to_dict(paths):
    dct_dir = {}
    for item in paths:
        p = dct_dir
        for x in item.split('/'):
            p = p.setdefault(x, {})
    return dct_dir


def path_to_text(paths):
    dct_dir = paths_to_dict(paths)
    text = dict_to_text(dct_dir)
    return text


def dict_to_text(dct_dir):
    """Converts dict to specially formatted string"""
    text = ""
    for key, d in dct_dir.items():
        text += key + ': ' + ' '.join(d.keys()) + '\n'
        text += dict_to_text(d)
    return text
