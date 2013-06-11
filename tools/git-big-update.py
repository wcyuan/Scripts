#!/usr/local/bin/python
#
"""
A simple helper script to pull changes through to multiple dependent branches
"""

from __future__ import absolute_import, division, with_statement

import argparse
import contextlib
import logging
import os
import subprocess

# ------------------------------------------------------------------

# Constants

TREE = [['/u/yuanc/proj/eomm',
         [['master',                    'git svn rebase'],
          ['rel_20130515-svn',          'git svn rebase'],
          ['git-default',               'git pull'],
          ['add-pcap',                  'git pull'],
          ['parallel_result_tree_diff', 'git pull']]],
        ['/u/yuanc/proj/scratcheomm',
         [['master',                    'git pull']]]
        #[WINDOWS_EOMM_DIR,
        # [['master',                    'git pull'],
        #  ['add-pcap',                  'git pull']]]
        ]

# ------------------------------------------------------------------

def main():
    _ = getopt()

    for (root, branches) in TREE:
        with chdir(root):
            for (branch, cmd) in branches:
                with checkout(branch):
                    Runner.run(cmd)

# ------------------------------------------------------------------

def getopt():
    parser = argparse.ArgumentParser()
    parser.add_argument('--no_write',
                        action='store_true',
                        help='Just print commands without running them')
    parser.add_argument('--verbose',
                        action='store_true',
                        help='Turn on verbose logging')
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    if args.no_write:
        Runner.NO_WRITE = True

    return args

# ------------------------------------------------------------------

class Runner(object):
    NO_WRITE = False

    @classmethod
    def run(cls, cmd, always=False, die_on_error=True):
        if cls.NO_WRITE and not always:
            print "NO WRITE: {0}".format(cmd)
            return

        print "Running:  {0}".format(cmd)
        process = subprocess.Popen(cmd.split(),
                                   stdout=subprocess.PIPE)
        try:
            output = process.communicate()[0]
        except subprocess.CalledProcessError as e:
            if die_on_error:
                raise
            else:
                print e
        return output

# ------------------------------------------------------------------

def get_current_branch():
    branches = Runner.run('git branch', always=True)
    for line in branches.split('\n'):
        if line.startswith('*'):
            return line.split()[1]

@contextlib.contextmanager
def checkout(branch):
    current_branch = get_current_branch()
    if current_branch == branch:
        yield
    else:
        Runner.run('git checkout {0}'.format(branch))
        yield
        Runner.run('git checkout {0}'.format(current_branch))

@contextlib.contextmanager
def chdir(directory):
    current_directory = os.getcwd()
    if current_directory == directory:
        yield
    else:
        print "cd {0}".format(directory)
        os.chdir(directory)
        yield
        print "cd {0}".format(current_directory)
        os.chdir(current_directory)

# ------------------------------------------------------------------

if __name__ == '__main__':
    main()
