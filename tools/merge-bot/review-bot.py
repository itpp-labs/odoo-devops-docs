#!/usr/bin/python
import sys
import requests
from github import Github


def main():

    if not len(sys.argv) == 5:
        print('Enter Github login, Github password, repository and PR number')
    else:
        github = Github(sys.argv[1], sys.argv[2])
        repo_name = sys.argv[3]
        pr_number = sys.argv[4]

        repo = github.get_repo(repo_name)
        pr = repo.get_pull(int(pr_number))
        print(pr.number)
        print(pr.changed_files)
        review_comments = []

        #print(commit)
        installable_modules = []
        for file in pr.get_files():
            if '__manifest__.py' in file.filename or '__openerp__.py' in file.filename:
                html = requests.get(file.raw_url, auth=('user', 'pass')).text
                #print(file.filename.split('/')[0], file.raw_url)
                if "'installable': True" in html or '"installable": True' in html:
                    installable_modules.append(file.filename.split('/')[0])
                    #print(file.filename.split('/')[0], 'installable')
        for file in pr.get_files():
            if 'changelog.rst' in file.filename and file.filename.split('/')[0] in installable_modules:
                print(file.filename)
                #print(file.patch)
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
                #print(comment_line)

        pr.create_review(commit=pr.get_commits()[pr.get_commits().totalCount-1],
                         body='Someone features needs to be tested'
                         , event='COMMENT', comments=review_comments)


if __name__ == "__main__":
    main()
