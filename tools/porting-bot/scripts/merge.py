#!/usr/bin/python
import os
from subprocess import Popen, PIPE, call
import argparse

VERSION_EMOJIS = {'8.0': ':eight:', '9.0': ':nine:', '10.0': ':one::zero:',
                  '11.0': ':one::one:', '12.0': ':one::two:', '13.0': ':one::three:'}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--upstream_remote", help="Remote where repository, in witch PR will be made, is located",
                        default='upstream')
    parser.add_argument("--origin_remote", help="Remote where repository, in which branch will be created, is located",
                        default='origin')
    parser.add_argument("--new_branch_name", help="Name for branch which will be created",
                        default=None)
    parser.add_argument('--auto_resolve', help="option for making some automatic resolving",
                        dest='auto_resolve', action='store_true')
    parser.add_argument('--auto_push', help="option for automatically push branch to origin repo",
                        dest='auto_push', action='store_true')
    parser.add_argument('--author', help="author info to use in commits", default=None)
    parser.add_argument("from_branch", help="Name of branch, from which merge will be made")
    parser.add_argument("in_branch", help="Name of branch, in which merge will be made")

    args = parser.parse_args()
    upstream_remote = args.upstream_remote
    origin_remote = args.origin_remote
    auto_resolve = args.auto_resolve
    auto_push = args.auto_push
    author = args.author
    from_branch = args.from_branch
    in_branch = args.in_branch
    new_branch_name = args.new_branch_name

    merge_branches(upstream_remote, origin_remote, auto_resolve, auto_push, author,
                   from_branch, in_branch, new_branch_name)


def merge_branches(upstream_remote, origin_remote, auto_resolve, auto_push, author,
                   from_branch, in_branch, new_branch_name):
    fetch(upstream_remote)
    call(['git', 'checkout', upstream_remote + '/' + in_branch])
    if new_branch_name is None:
        new_branch_name = in_branch + '-automerge-' + get_last_commit_on_branch(upstream_remote + '/' + from_branch)
    print(new_branch_name)
    if branch_exists(new_branch_name):
        abort_merge()
        branch_delete(new_branch_name)

    call(['git', 'checkout', '-b', new_branch_name])

    conflict_files = merge(upstream_remote + '/' + from_branch)
    print(len(conflict_files))
    if len(conflict_files) > 0:
        commits = get_commits()
        for commit in commits:
            abort_merge()
            reset_to_commit(commit)
            conflict_files = merge(upstream_remote + '/' + from_branch)
            print(commit, len(conflict_files))
            if len(conflict_files) == 0:
                break

        conflict_files = merge(upstream_remote + '/' + in_branch)

        if auto_resolve:
            print(conflict_files)
            print('Resolving conflicts...')
            abort_merge()

            solve_translation_conflicts(conflict_files, in_branch)

            commit_all(':peace_symbol:' + VERSION_EMOJIS[in_branch] +
                       ' translation conflicts are automatically resolved',
                       author)
        else:
            abort_merge()

    if auto_push:
        push_with_upstream(origin_remote, new_branch_name)
        print(str(new_branch_name), 'pushed to', origin_remote)


def solve_translation_conflicts(conflict_files, checkout_branch):
    for conflict_file in conflict_files:
        if conflict_file.endswith('.pot'):
            checkout_one_file(conflict_file, checkout_branch)


def checkout_one_file(file_path, branch):
    call(['git', 'checkout', branch, '--', file_path])


def get_remote_name(name):
    proc = Popen(['git', 'remote' 'get-url', name], stdout=PIPE, stderr=PIPE)
    return proc.communicate().split(':')[-1].split('/')[0]


def fetch(remote):
    call(['git', 'fetch', remote])


def push_with_upstream(remote, branch):
    call(['git', 'push', '--set-upstream', remote, branch])


def commit_file(file_name, message):
    call(['git', 'commit', file_name, '-m', message])


def commit_all(message, author=None):
    if author is None:
        call(['git', 'commit', '-a', '-m', message])
    else:
        call(['git', 'commit', '-a', '--author', author, '-m', message])


def branch_exists(branch_name):
    proc = Popen(['git', 'branch', '--list', branch_name], stdout=PIPE, stderr=PIPE)
    str = proc.communicate()[0].decode("utf-8")
    print(str)
    print('Branch exist' if str else 'Branch does not exist')
    return True if str else False


def branch_delete(branch_name):
    call(['git', 'branch', '-D', branch_name])


def merge(branch):
    with open(os.devnull, 'w') as devnull:
        call(['git', 'merge', branch], stdout=devnull)
    proc = Popen(['git', 'diff', '--name-only', '--diff-filter=U'], stdout=PIPE, stderr=PIPE)
    return proc.communicate()[0].decode("utf-8").split('\n')[:-1]


def diff():
    proc = Popen(['git', 'diff'], stdout=PIPE, stderr=PIPE)
    return proc.communicate()[0]


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


if __name__ == "__main__":
    main()
