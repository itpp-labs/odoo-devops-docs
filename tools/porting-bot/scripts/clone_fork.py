#!/usr/bin/python
"""Script for cloning fork of github repo."""

import argparse
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
    parser.add_argument("base_repo_name", help="Name of repository fork of witch will be cloned."
                                               " Name should not include owner name")
    parser.add_argument("clone_path", help="Path where repo will be cloned")

    args = parser.parse_args()
    github_login = args.github_login
    github_password = args.github_password
    github_token = args.github_token
    base_repo_name = args.base_repo_name
    clone_path = args.clone_path

    clone_repo_fork(github_login, github_password, github_token, base_repo_name, clone_path)


def clone_repo_fork(github_login, github_password, github_token,
                    repo_name, clone_path):
    """
    Clones fork of specified git repository.

    :param github_login:
        Login from github account.
    :param github_password:
        Password from github account.
    :param github_token:
        Token from github account. If token or login/password not specified will be taken from
        GITHUB_TOKEN_FOR_BOT environmental variable.
    :param repo_name:
        Name of repo to clone.
    :param clone_path:
        Name of repository fork of witch will be cloned.
    """

    if github_login is not None and github_password is not None:
        github = Github(github_login, github_password)
    elif github_token is not None:
        github = Github(github_token)
    else:
        print('Please specify github login/password or token.')

    user = github.get_user()
    repos = user.get_repos()

    repo_found = False

    for fork in repos:
        if repo_name == fork.name:
            repo_found = True
            fork_url = fork.clone_url.replace('https://', 'https://{}@'.format(github_token))
            source = fork.source
            source_url = source.clone_url.replace('https://', 'https://{}@'.format(github_token))

            print('Cloning {} in {}'.format(fork_url, clone_path))
            call(['git', 'clone', fork_url, clone_path])
            os.chdir(clone_path)
            call(['git', 'remote', 'add', 'upstream', source_url])

    if not repo_found:
        print('Repo is not found!')


if __name__ == "__main__":
    main()
