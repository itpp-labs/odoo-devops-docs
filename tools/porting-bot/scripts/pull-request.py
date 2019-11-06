#!/usr/bin/python
import argparse
import datetime
import os
from github import Github
from subprocess import call


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--github_login", help="Login from github account", default=None)
    parser.add_argument("--github_password", help="Password from github account", default=None)
    parser.add_argument("--github_token",
                        help="Token from github account. Token or login/passord not specified"
                             " will be taken from GITHUB_TOKEN_FOR_BOT environmental variable",
                        default=os.getenv("GITHUB_TOKEN_FOR_BOT"))
    parser.add_argument("base_repo_name", help="Name of repository where PR will be made")
    parser.add_argument("base_branch", help="Name of branch, in which PR will be made")
    parser.add_argument("forked_user", help="Name of the user who own a fork where branch is located")
    parser.add_argument("head_branch", help="Name of branch, from where PR will be made")
    parser.add_argument("original_pr_title", "name of initial title from which changes are taken. "
                                             "This param needed for webhook", default='')
    parser.add_argument(
        "--webhook_when_porting_pr_exists",
        help="URL for webhook when porting PR exists. Default value is \"github-instance-profile-name\".",
        default='')
    parser.add_argument(
        "--webhook_when_porting_pr_created",
        help="URL for webhook when porting PR created. Default value is \"github-instance-profile-name\".",
        default='')

    args = parser.parse_args()
    github_login = args.github_login
    github_password = args.github_password
    github_token = args.github_token
    base_repo_name = args.base_repo_name
    base_branch = args.base_branch
    forked_user = args.forked_user
    head_branch = args.head_branch
    hook_exists = args.webhook_when_porting_pr_exists,
    hook_created = args.webhook_when_porting_pr_created
    original_pr_title = args.original_pr_title

    pull_request(github_login, github_password, github_token, base_repo_name, base_branch, forked_user, head_branch, hook_exists, hook_created, original_pr_title)


def pull_request(github_login, github_password, github_token, base_repo_name, base_branch, forked_user, head_branch, hook_exists, hook_created, original_pr_title):

    if github_login is not None and github_password is not None:
        github = Github(github_login, github_password)
    elif github_token is not None:
        github = Github(github_token)
    else:
        print('Please specify github login/password or token')

    repo = github.get_repo(base_repo_name)
    write_in_log('arguments is passed')
    pull_requests = repo.get_pulls()
    merge_pr_exists = False
    existing_pr_title = None

    for pr in pull_requests:
        if 'Auto merge {}:'.format(forked_user) in pr.title and '-{}'.format(base_branch) in pr.title:
            merge_pr_exists = True
            existing_pr_title = pr.title
            write_in_log('there is already PR')

    if not merge_pr_exists:
        repo.create_pull(title="Auto merge {}:{}-{}".format(forked_user, head_branch, base_branch),
                         body="This is auto merge from {}:{} to {}".format(forked_user, head_branch, base_branch),
                         base=base_branch, head=forked_user + ':' + head_branch)
        write_in_log('pull created')
        if hook_created is not '':
            call(['curl', '-X', 'POST', hook_exists, '-H',
                  '"Content-Type: application/json"', '-d',
                  '{"value1":"{}","value2":"{}","value3":"{}"}'.format(
                      original_pr_title, "Auto merge {}:{}-{}".format(forked_user, head_branch, base_branch), github_login)])

    elif hook_exists is not '':
        call(['curl', '-X', 'POST', hook_exists, '-H',
              '"Content-Type: application/json"', '-d',
              '{"value1":"{}","value2":"{}","value3":"{}"}'.format(original_pr_title, existing_pr_title, github_login)])


def write_in_log(log_message):
    """
    Writes log messages to log file.

    :param log_message:
        Text of the message.
    """

    now = datetime.datetime.now()
    if not os.path.isdir('/home/ec2-user/logs-github-bot/'):
        os.mkdir('/home/ec2-user/logs-github-bot/')
    with open('/home/ec2-user/logs-github-bot/{}.txt'.format(now.strftime('%Y-%m-%d')), 'a') as logfile:
        logfile.write('{} {}\n'.format(now.strftime('%Y-%m-%d %H:%M:%S'), log_message))


if __name__ == "__main__":
    main()
