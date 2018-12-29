#!/usr/bin/python
import argparse
import os
from github import Github


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("--github_login", help="Login from github account", default=None)
    parser.add_argument("--github_password", help="Password from github account", default=None)
    parser.add_argument("--github_token",
                        help="Token from github account. Token or login/passord not specified"
                             " will be taken from MERGE_BOT_GITHUB_TOKEN environmental variable",
                        default=os.getenv("MERGE_BOT_GITHUB_TOKEN"))
    parser.add_argument("base_repo_name", help="Name of repository where PR will be made")
    parser.add_argument("base_branch", help="Name of branch, in which merge will be made")
    parser.add_argument("forked_user", help="Name of the user who own a fork where branch is located")
    parser.add_argument("head_branch", help="Name of branch, from where merge will be made")

    args = parser.parse_args()
    github_login = args.github_login
    github_password = args.github_password
    github_token = args.github_token
    base_repo_name = args.base_repo_name
    base_branch = args.base_branch
    forked_user = args.forked_user
    head_branch = args.head_branch

    if github_login is not None and github_password is not None:
        github = Github(github_login, github_password)
    elif github_token is not None:
        github = Github(github_token)
    else:
        print('Please specify github login/password or token')

    repo = github.get_repo(base_repo_name)

    repo.create_pull(title="Title", body="Body", base=base_branch, head=forked_user + ':' + head_branch)


if __name__ == "__main__":
    main()
