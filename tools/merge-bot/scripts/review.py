#!/usr/bin/python
import argparse
import os
import requests
from github import Github


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("--github_login", help="Login from github account", default=None)
    parser.add_argument("--github_password", help="Password from github account", default=None)
    parser.add_argument("--github_token",
                        help="Token from github account. Token or login/passord not specified"
                             " will be taken from MERGE_BOT_GITHUB_TOKEN environmental variable",
                        default=os.getenv("MERGE_BOT_GITHUB_TOKEN"))
    parser.add_argument("repo_name", help="Name of repository where review will be made")
    parser.add_argument("pr_number", help="Number of PR in which review will be made")
    args = parser.parse_args()
    github_login = args.github_login
    github_password = args.github_password
    github_token = args.github_token
    repo_name = args.repo_name
    pr_number = args.pr_number

    if github_login is not None and github_password is not None:
        github = Github(github_login, github_password)
    elif github_token is not None:
        github = Github(github_token)
    else:
        print('Please specify github login/password or token')
        exit()

    repo = github.get_repo(repo_name)
    pr = repo.get_pull(int(pr_number))
    review_comments = []
    updated_modules = set()
    installable_modules = set()
    for file in pr.get_files():
        module_name = file.filename.split('/')[0]
        if module_name not in updated_modules:
            updated_modules.add(module_name)

        if '__manifest__.py' in file.filename:
            html = requests.get(file.raw_url).text
            if "'installable': True" in html or '"installable": True' in html:
                installable_modules.add(module_name)

    for file in pr.get_files():
        if 'changelog.rst' in file.filename and file.filename.split('/')[0] in installable_modules:
            print(file.filename)
            comment_line = 0
            change_started = False
            for line in file.patch.split('\n')[1:]:
                if change_started:
                    if not line.startswith('+'):
                        break
                else:
                    if line.startswith('+'):
                        change_started = True
                comment_line += 1
            review_comments.append({'path': file.filename,
                                    'position': comment_line,
                                    'body': 'Someone has to test it'})

    review_body = '{} modules {} updated:\n' \
                  '* {}\n\n'.format(len(updated_modules),
                                    'is' if len(updated_modules) == 1 else 'are',
                                    '\n* '.join(updated_modules))

    if review_comments:
        review_body += '{} features needs to be tested.'.format(len(review_comments))
        pr.create_review(commit=pr.get_commits()[pr.get_commits().totalCount - 1],
                         body=review_body
                         , event='COMMENT', comments=review_comments)
    else:
        review_body += 'No new features need to be tested.'
        pr.create_review(commit=pr.get_commits()[pr.get_commits().totalCount - 1],
                         body=review_body
                         , event='COMMENT')


if __name__ == "__main__":
    main()
