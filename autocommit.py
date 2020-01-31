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


commit_styles = ['All files in one commit', "Every file in a single commit"]
all_files = "*ALL"


class GitUiOpts:
    def __init__(self, path, remote_target="origin"):
        self.committer = None
        self.repo_path = path
        self.repo = Repo(self.repo_path)
        self.unstaged = []
        self.staged = []
        self.remote_url = self.repo.get_config().get(
            ('remote', remote_target), 'url').decode()
        self.remote_url_credentials = None

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

    def push_once(self):
        remote_url = self.remote_url if self.remote_url_credentials is None else self.remote_url_credentials
        porcelain.push(
            self.repo, remote_location=remote_url, refspecs="master")
        self.staged = []

    def push(self):
        is_pushed = False
        while is_pushed is False:
            try:
                self.push_once()
            except:
                username = self.simple_input(content="Username : ")
                password = self.simple_input(content="Password : ")
                self.remote_url_credentials = "//{0}:{1}@".format(
                    username, password).join(self.remote_url.split('//'))
                self.push_once()
            finally:
                is_pushed = True

    def get_committer(self):
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

    def simple_input(self, content):
        print(content)
        return input()

    def select_input(self, keyword, message, choices):
        questions = [
            inquirer.List(keyword,
                          message=message,
                          choices=choices,
                          ),
        ]
        answers = inquirer.prompt(questions)
        return answers[keyword]


def sys_exit(signum, frame):
    sys.exit()


def main():
    signal.signal(signal.SIGTSTP, sys_exit)
    while True:
        ap = GitUiOpts(path=".")
        if find_executable("git") is not None:
            username, mail = ap.get_committer()
            ap.committer = "{0} <{1}>".format(username, mail)
        else:
            ap.committer = ap.simple_input(
                content="Who is the author ?\n eg: \"PABlond <pierre-alexis.blond@live.fr>\"")

        ap.get_unstaged()

        if len(ap.unstaged) == 0:
            sys.exit()

        file_to_commit = ap.select_input(
            keyword="file", message="What file do you want to commit?", choices=[all_files] + ap.unstaged)
        if file_to_commit == all_files:
            commit_style = ap.select_input(
                keyword="style", message="How do you want to commit unstaged files?", choices=commit_styles)
            if commit_style == commit_styles[0]:
                title = ap.simple_input(
                    content="Choose a title for your commit : ")
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
