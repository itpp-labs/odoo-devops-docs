#!/usr/bin/python
import os
import sys
from subprocess import Popen, PIPE, call
import argparse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--upstream_remote", help="Remote where repository, in witch PR will be made, is located", default='upstream')
    parser.add_argument("--origin_remote", help="Remote where repository, in which branch will be created, is located", default='origin')
    parser.add_argument("from_branch", help="Name of branch, from which merge will be made")
    parser.add_argument("in_branch", help="Name of branch, in which merge will be made")

    parser.add_argument("github_login", help="Login from github account")
    parser.add_argument("github_password", help="Password from github account")

    args = parser.parse_args()
    upstream_remote = args.upstream_remote
    origin_remote = args.origin_remote
    from_branch = args.from_branch
    in_branch = args.in_branch

    github_login = args.github_login
    github_password = args.github_passwor

    #repo_name = get_repo_name()
    #upstream = 'git@github.com:' + upstream_account + '/' + repo_name + '.git'
    #origin = 'git@github.com:' + origin_account + '/' + repo_name + '.git'

    fetch(upstream_remote)
    call(['git', 'checkout', upstream_remote + '/' + in_branch])

    new_branch_name = in_branch + '-' + get_last_commit_on_branch(upstream_remote + '/' + from_branch)
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

        #for file_name in conflict_files:
        #    print(file_name)
        #    if '__manifest__.py' in file_name:
        #        if file_name.replace('__manifest__.py', '') + 'doc/changelog.rst' not in conflict_files:
        #            conflicts, conflict_lines = find_conflicts(file_name)
        #            if len(conflict_lines) == 1:
        #                if '"version"' in conflicts[0][0] and '"version"' in conflicts[0][1]:
        #                    solve_conflict(file_name, conflict_lines[0], solve_version(conflicts[0][0], conflicts[0][1]))

        solution_files = []
        solutions = []
        solution_lines = []
        for file_name in conflict_files:
            print(file_name)
            if '__manifest__.py' in file_name:
                if file_name.replace('__manifest__.py', '') + 'doc/changelog.rst' not in conflict_files:
                    conflicts, conflict_lines = find_conflicts(file_name)
                    if len(conflict_lines) == 1:
                        if '"version"' in conflicts[0][0] and '"version"' in conflicts[0][1]:
                            solution_files.append(file_name)
                            solutions.append(solve_version(conflicts[0][0], conflicts[0][1]))
                            solution_lines.append(conflict_lines[0])

        abort_merge()

        #for i in range(len(solutions)):
        #    solve_conflict(solution_files[i], solution_lines[i], solutions[i])

    #call(['git', 'status'])


def clone_repo(url):
    call(['git', 'clone', url])


def get_repo_name():
    proc = Popen(['basename', "'git rev-parse --show-toplevel'"], stdout=PIPE, stderr=PIPE)
    return proc.communicate()[0]


def get_remote_name(name):
    proc = Popen(['git', 'remote' 'get-url', name], stdout=PIPE, stderr=PIPE)
    return proc.communicate().split(':')[-1].split('/')[0]


def add_remote(name, remote):
    call(['git', 'remote', 'add', name, remote])


def fetch(remote):
    call(['git', 'fetch', remote])


def pull(remote):
    call(['git', 'pull', remote])


def branch_exists(branch_name):
    #print('git', 'branch', '--list', branch_name)
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


def find_conflicts(file_name):
    with open(file_name) as file:
        i = 0
        conflict_lines = []
        conflicts = []
        conflict_found = False
        for line in file:
            if not conflict_found:
                if '<<<<<<< ' in line:
                    conflict_lines.append([0, 0, 0, 0])
                    conflicts.append([''])
                    conflict_lines[-1][0] = i
                    conflict_found = True
            else:
                if '=======\n' in line:
                    conflict_lines[-1][1] = i
                    conflict_lines[-1][2] = i
                    conflicts[-1].append('')
                elif '>>>>>>> ' in line:
                    conflict_found = False
                    conflict_lines[-1][3] = i
                else:
                    conflicts[-1][-1] += line
            i += 1
    return conflicts, conflict_lines


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


def solve_conflict(file_name, conflict_lines, solution):
    solution_lines = solution.split('\n')[0:-1]
    with open(file_name, 'r') as file:
        data = file.readlines()
        del data[conflict_lines[0]: conflict_lines[-1] + 1]
        for i in range(len(solution_lines)):
            data.insert(conflict_lines[0] + i, solution_lines[i])

    with open(file_name, 'w') as file:
        file.writelines(data)

    print(file_name, 'conflict solved')


def make_pr(github_login, github_password, remote):
    from github import Github
    github = Github(github_login, github_password)
    repo = github.get_repo("PyGithub/PyGithub")


if __name__ == "__main__":
    main()
