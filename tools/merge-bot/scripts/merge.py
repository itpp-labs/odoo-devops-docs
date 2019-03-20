#!/usr/bin/python
import os
import sys
from subprocess import Popen, PIPE, call
import argparse

VERSION_EMOJIS = {'8.0': ':eight:', '9.0': ':nine:', '10.0': ':one::zero:', '11.0': ':one::one:', '12.0': ':one::two:'}


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
    parser.add_argument("from_branch", help="Name of branch, from which merge will be made")
    parser.add_argument("in_branch", help="Name of branch, in which merge will be made")

    args = parser.parse_args()
    upstream_remote = args.upstream_remote
    origin_remote = args.origin_remote
    auto_resolve = args.auto_resolve
    auto_push = args.auto_push
    from_branch = args.from_branch
    in_branch = args.in_branch
    new_branch_name = args.new_branch_name

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

        merge(upstream_remote + '/' + in_branch)

        if auto_resolve:
            conflicts = find_resolvable_conflicts()
            abort_merge()

            for conflict in conflicts:
                solve_conflict(conflict)

            commit_all(':peace_symbol:' + VERSION_EMOJIS[in_branch] + ' some version conflicts in manifests are'
                                                                      ' automatically resolved')
        else:
            abort_merge()

    if auto_push:
        push_with_upstream(origin_remote, new_branch_name)
        print(str(new_branch_name), 'pushed to', origin_remote)


def clone_repo(url):
    call(['git', 'clone', url])


def get_repo_name():
    proc = Popen(['basename', "'git rev-parse --show-toplevel'"], stdout=PIPE, stderr=PIPE)
    return proc.communicate()[0]


def get_remote_name(name):
    proc = Popen(['git', 'remote' 'get-url', name], stdout=PIPE, stderr=PIPE)
    return proc.communicate().split(':')[-1].split('/')[0]


def fetch(remote):
    call(['git', 'fetch', remote])


def push_with_upstream(remote, branch):
    call(['git', 'push', '--set-upstream', remote, branch])


def commit_file(file_name, message):
    call(['git', 'commit', file_name, '-m', message])


def commit_all(message):
    call(['git', 'commit', '-a', '-m', message])


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


def find_resolvable_conflicts():
    conflicts = []
    file_names = []
    conflict_file = ''
    file_found = False
    conflict_found = False
    lines = diff().split('\n')
    line_num = 0
    conflict_line = 0
    while line_num < len(lines):
        if lines[line_num].startswith('diff --cc '):
            file_names.append(lines[line_num][10:])
            if lines[line_num].endswith('__manifest__.py'):
                conflict_file = file_names[-1]
                file_found = True

                while not lines[line_num].startswith('@@@ '):
                    line_num += 1
                begin = lines[line_num].split(' ')[1].split(',')[0][1:]
                conflict_line = int(begin) - 1
            else:
                file_found = False
        elif file_found:

            if not conflict_found:
                if lines[line_num].startswith('++<<<<<<< '):
                    conflicts.append({'file': conflict_file, 'body1': '', 'body2': '', 'lines': [], 'solution': ''})
                    conflicts[-1]['lines'].append(conflict_line)
                    conflict_found = True
            else:
                if lines[line_num].startswith('++======='):
                    conflicts[-1]['lines'].append(conflict_line)
                elif lines[line_num].startswith('++>>>>>>> '):
                    conflicts[-1]['lines'].append(conflict_line)
                    conflict_found = False
                else:
                    if len(conflicts[-1]['lines']) == 1:
                        conflicts[-1]['body1'] += lines[line_num][2:] + '\n'
                    else:
                        conflicts[-1]['body2'] += lines[line_num][2:] + '\n'
            conflict_line += 1
        line_num += 1

    for conflict in conflicts[:]:
        if conflict['file'].endswith('__manifest__.py'):
            if conflict['file'].replace('__manifest__.py', 'doc/changelog.rst') not in file_names \
                    and '"version"' in conflict['body1'] and '"version"' in conflict['body2']:

                conflict['solution'] = solve_version(conflict['body1'], conflict['body2'])

                print(conflict)
            else:
                conflicts.remove(conflict)

    return conflicts


def parse_version(line):
    return line.split('"')[-2]


def solve_version(old_version, new_version):
    parsed_old = parse_version(old_version).split('.')
    parsed_new = parse_version(new_version).split('.')
    odoo_version = parsed_new[0] + '.' + parsed_new[1]

    module_version = ''
    for i in range(2, len(parsed_new)):
        if parsed_new[i] > parsed_old[i]:
            for j in range(i, len(parsed_new)):
                module_version += '.' + parsed_new[j]
            break
        elif parsed_new[i] < parsed_old[i]:
            for j in range(i, len(parsed_new)):
                module_version += '.' + parsed_old[j]
            break
        else:
            module_version += '.' + parsed_new[i]

    version = odoo_version + module_version

    version_line = new_version.replace(parse_version(new_version), version)

    return version_line


def solve_conflict(conflict):
    solution_lines = conflict['solution'].split('\n')[0:-1]
    with open(conflict['file'], 'r') as file:
        data = file.readlines()
        del data[conflict['lines'][0] + 1: conflict['lines'][1]]
        for i in range(len(solution_lines)):
            data.insert(conflict['lines'][0] + i + 1, solution_lines[i] + '\n')

    with open(conflict['file'], 'w') as file:
        file.writelines(data)

    print(conflict['file'], 'conflict solved')


if __name__ == "__main__":
    main()
