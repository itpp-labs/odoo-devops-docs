#!/usr/bin/python
import os
from subprocess import Popen, PIPE, call

FORK = 'Rusllan'
FROM = 'it-projects-llc'
REPO_NAME = 'pos-addons'
FROM_BRANCH = 'upstream/10.0'
IN_BRANCH = '11.0'

ORIGIN = 'git@github.com:' + FORK + '/' + REPO_NAME + '.git'
UPSTREAM = 'git@github.com:' + FROM + '/' + REPO_NAME + '.git'


def clone_repo(url):
    call(['git', 'clone', url])


def cd_in_repo():
    os.chdir(os.getcwd() + '/' + REPO_NAME)


def add_remote(name, remote):
    call(['git', 'remote', 'add', name, remote])


def fetch(remote):
    call(['git', 'fetch', remote])


def pull(remote):
    call(['git', 'pull', remote])


def branch_exists(branch_name):
    proc = Popen(['git', 'branch', '--list ', branch_name], stdout=PIPE, stderr=PIPE)
    return proc.communicate()[0].decode("utf-8") != ''


def branch_delete(branch_name):
    call(['git', 'branch', '-D', branch_name])


def merge(branch):
    with open(os.devnull, 'w') as devnull:
        call(['git', 'merge', branch], stdout=devnull)
    proc = Popen(['git', 'diff', '--name-only', '--diff-filter=U'], stdout=PIPE, stderr=PIPE)
    return proc.communicate()[0].decode("utf-8")


def abort_merge():
    with open(os.devnull, 'w') as devnull:
        call(['git', 'merge', '--abort'], stdout=devnull)


def get_commits():
    proc = Popen(['git', 'log', '--pretty=format:%H'], stdout=PIPE, stderr=PIPE)
    return proc.communicate()[0].decode("utf-8").split('\n')[0:-1]


def get_last_commit_on_branch(branch_name):
    proc = Popen(['git', 'log', '--format=%H', branch_name], stdout=PIPE, stderr=PIPE)
    return proc.communicate()[0].decode("utf-8").split('\n')[0]


def reset_to_commit(commit):
    with open(os.devnull, 'w') as devnull:
        call(['git', 'reset', '--hard', commit], stdout=devnull)


def main():

    if os.path.exists(REPO_NAME):
        cd_in_repo()
        abort_merge()
        new_branch_name = IN_BRANCH + '-' + get_last_commit_on_branch(FROM_BRANCH)
        fetch('upstream')
        branch_delete(new_branch_name)
    else:
        clone_repo(ORIGIN)
        cd_in_repo()
        add_remote('upstream', UPSTREAM)
        fetch('upstream')
        new_branch_name = IN_BRANCH + '-' + get_last_commit_on_branch(FROM_BRANCH)

    print(new_branch_name)

    call(['git', 'checkout', 'origin/' + IN_BRANCH])
    call(['git', 'checkout', '-b', new_branch_name])

    conflict_files = merge(FROM_BRANCH)
    print(len(conflict_files))

    commits = get_commits()
    for commit in commits:
        abort_merge()
        reset_to_commit(commit)
        conflict_files = merge(FROM_BRANCH)
        print(commit, len(conflict_files))
        if len(conflict_files) == 0:
            break

    conflict_files = merge('origin/' + IN_BRANCH)
    print(conflict_files)

    call(['git', 'status'])


if __name__ == "__main__":
    main()
