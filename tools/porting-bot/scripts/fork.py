#!/usr/bin/python
"""Script for forking github repo."""

import argparse
import os
from github import Github


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("--github_login", help="Login from github account", default=None)
    parser.add_argument("--github_password", help="Password from github account", default=None)
    parser.add_argument("--github_token",
                        help="Token from github account. Token or login/passord not specified"
                             " will be taken from GITHUB_TOKEN_FOR_BOT environmental variable",
                        default=os.getenv("GITHUB_TOKEN_FOR_BOT"))
    parser.add_argument("base_repo_name", help="Name of repository fork of witch will be made")

    args = parser.parse_args()
    github_login = args.github_login
    github_password = args.github_password
    github_token = args.github_token
    base_repo_name = args.base_repo_name

    fork(github_login, github_password, github_token, base_repo_name)


def fork(github_login, github_password, github_token, base_repo_name):
    """
    Forks specified repository. If fork exists, do nothing.

    :param github_login:
        Login from github account.
    :param github_password:
        Password from github account.
    :param github_token:
        Token from github account. If token or login/password not specified will be taken from
        GITHUB_TOKEN_FOR_BOT environmental variable.
    :param base_repo_name:
        Name of repository where PR will be made.
    """

    if github_login is not None and github_password is not None:
        github = Github(github_login, github_password)
    elif github_token is not None:
        github = Github(github_token)
    else:
        print('Please specify github login/password or token.')

    repo = github.get_repo(base_repo_name)

    github_user = github.get_user()
    github_user.create_fork(repo)


if __name__ == "__main__":
    main()
