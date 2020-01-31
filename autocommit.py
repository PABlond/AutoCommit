import sys
import signal
import subprocess
from distutils.spawn import find_executable
import inquirer
from dulwich.repo import Repo
from dulwich.diff_tree import tree_changes
from dulwich import porcelain
import dulwich
import numpy as np


commit_styles = ['All in one commit', "Every file in one commit"]


class GitOpts:
    def __init__(self, path, committer, remote_target="origin"):
        self.committer = committer
        self.repo_path = path
        self.repo = Repo(self.repo_path)
        self.unstaged = []
        self.staged = []
        self.remote_url = self.repo.get_config().get(
            ('remote', remote_target), 'url').decode()

    def get_unstaged(self):
        status = porcelain.status(self.repo.path)
        for x in np.concatenate((status.untracked, status.unstaged)):
            try:
                x = x.decode()
            except:
                pass
            finally:
                self.unstaged.append(x)

    def get_staged(self):
        staged = porcelain.status(self.repo.path).staged
        for type_file in ['delete', 'add', 'modify']:
            for filepath in staged[type_file]:
                self.staged.append({
                    "type": type_file,
                    "path": filepath.decode()
                })

    def stage_file(self, filepath):
        if filepath in self.unstaged:
            self.repo.stage([filepath])

    def commit_all_files(self, commit_title):
        self.repo.do_commit(
            commit_title.encode(),
            committer=self.committer.encode()
        )
        print(commit_title)

    def commit_file(self):
        self.get_staged()
        for file_to_commit in self.staged:
            commit_title = '{} {}'.format(
                file_to_commit['type'], file_to_commit['path'].split('/')[-1])
            self.repo.do_commit(
                commit_title.encode(),
                committer=self.committer.encode()
            )
            print(commit_title)

    def push(self):
        porcelain.push(
            self.repo, remote_location=self.remote_url, refspecs="master")
        self.staged = []


def is_git():
    return find_executable("git") is not None


def get_committer():
    username, mail = "", ""
    result = subprocess.run(
        ["git", "config", "--list"], stdout=subprocess.PIPE)
    for row in result.stdout.decode().split("\n"):
        row_formatted = row.split("=")
        if len(row_formatted) == 2:
            row_key = row_formatted[0]
            row_value = row_formatted[1]
            if row_key == "user.name":
                username = row_value
            elif row_key == "user.email":
                mail = row_value

    return username, mail


def simple_input(content):
    print(content)
    return input()


def set_committer():
    return simple_input(
        content="Who is the author ?\n eg: \"PABlond <pierre-alexis.blond@live.fr>\"")


def files_to_commit(unstaged_files):
    questions = [
        inquirer.List('file',
                      message="What file do you want to commit?",
                      choices=['*ALL'] + unstaged_files,
                      ),
    ]
    answers = inquirer.prompt(questions)
    return answers["file"]


def commit_all_style():
    questions = [
        inquirer.List('style',
                      message="How do you want to commit unstaged files?",
                      choices=commit_styles,
                      ),
    ]
    answers = inquirer.prompt(questions)
    return answers["style"]


def get_commit_title():
    return simple_input(content="Choose a title for your commit : ")


def handler(signum, frame):
    sys.exit()


def main():
    signal.signal(signal.SIGTSTP, handler)
    while True:
        committer = None
        if is_git():
            username, mail = get_committer()
            committer = "{} <{}>".format(username, mail)
        else:
            committer = set_committer()

        print(committer)
        ap = GitOpts(path=".", committer=committer)
        ap.get_unstaged()

        if len(ap.unstaged) == 0:
            sys.exit()

        file_to_commit = files_to_commit(unstaged_files=ap.unstaged)
        if file_to_commit == "*ALL":
            commit_style = commit_all_style()
            if commit_style == commit_styles[0]:
                title = get_commit_title()
                for filepath in ap.unstaged:
                    ap.stage_file(filepath=filepath)
                ap.commit_all_files(commit_title=title)
                ap.push()
            else:
                for filepath in ap.unstaged:
                    ap.stage_file(filepath=filepath)
                    ap.commit_file()
                ap.push()
        else:
            ap.commit_file(filepath=file_to_commit)
            ap.push()

if __name__ == '__main__':
    main()