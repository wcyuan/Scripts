#!/usr/bin/env python
"""
git-cherry-push.py [--force] [revision|file]

Description: cherry-pick a single local commit and push it

This script creates a new branch, cherry-picks one commit into that
branch, then pushes just that one commit.

Run with --no_write to see what commands would be run without actually
running the commands.

This command always pushes a single, entire commit.  If you run the
command on a file, it will find the last commit that modified that
file, and push that commit.  If that commit modifies multiple files,
then changes to all of those files will be pushed at once.

When run with no arguments, it will attempt to push the last commit in
the currently active branch.

Details:

Like for most git commands, the current working directory must be in
the repository you want to push from.

If you have outstanding changes to your working tree when this runs,
those changes will be stashed while this script runs, and unstashed
after it is done.

By default, we get the name of the remote repo from the branch that
the currently active branch is tracking.  This remote repo would
normally have the name 'origin', but people may have given it any name
they want.  Thus, the currently active branch should be a tracking
branch.  To override this, you can provide the remote repo and branch
to push to with the --upstream option.

We require that the currently active branch tracks the master branch
(and that that branch is called 'master').  If you run with --force,
then we will push to whatever branch the active branch tracks, even if
it isn't called 'master'.

After pushing the commit, we will do a pull on the currently active
branch in the local repository.  We assume that the current branch is
tracking the same branch that you pushed to, so you'll want the
current branch to be updated to reflect the change you just pushed.

Created by: Conan Yuan (yuanc), 20120830
"""
#
#

from __future__ import absolute_import, division, with_statement

from   contextlib               import contextmanager
from   optparse                 import OptionParser

# For GitPython documentation, try
# https://groups.google.com/forum/?fromgroups#!forum/git-python
from   git                      import Repo, BadObject

import os
import re

__version__ = "$Revision: 1.15 $"

##################################################################

FLAG_NO_WRITE = False

def main():
    """
    Main body of the script.
    """
    opts, args = getopts()

    repo = Repo(opts.repo)

    if len(args) == 0:
        rev = repo.head.commit
    else:
        rev = args[0]

    rev = get_revision(repo, rev)

    push_to_master(repo, rev, opts.remote, opts.upstream, opts.force)


def getopts():
    """
    Parse the command-line options
    """
    parser = OptionParser()
    # Script-specific options

    parser.add_option('--no_write',
                      action='store_true',
                      help="Print the commands to run without running them")
    parser.add_option('--force',
                      action='store_true',
                      help="Don't require the upstream "
                      "branch be called 'master'")
    parser.add_option('--remote',
                      help='The remote repo to push to')
    parser.add_option('--upstream',
                      help='The remote branch to push to')
    parser.add_option('--repo',
                      help='The repo to cherry-pick from')

    opts, args = parser.parse_args()

    if len(args) > 1:
        raise ValueError("Too many arguments")

    # Allow the user to specify the remote repo and branch together as
    # remote/branch
    if opts.remote is None:
        if opts.upstream is not None:
            if '/' in opts.upstream:
                (opts.remote, opts.upstream) = opts.upstream.split('/', 2)


    if opts.no_write:
        global FLAG_NO_WRITE
        FLAG_NO_WRITE = True

    return (opts, args)

##################################################################
# Functions for doing a cherry-pick and a push (given the branch to
# push to)
#

def git_cmd(repo, cmd, *args):
    '''
    Run a git command.  But, if no_write is given, then just print the
    command to run without running it.
    '''
    cmdline = 'git %s %s' % (
        cmd, ' '.join(str(a) for a in args))
    if FLAG_NO_WRITE:
        print "Would run: " + cmdline
    else:
        cmd = cmd.replace('-', '_')
        print "Running  : " + cmdline
        getattr(repo.git, cmd)(*args)

def temp_branch_name(repo):
    """
    Returns a name which is not currently being used as a branch, so
    that we can safely create a new temporary branch with this name.
    """
    branches = repo.branches
    number = 0
    while True:
        temp = 'temp%d' % number
        if temp not in branches:
            return temp
        number += 1

@contextmanager
def temp_branch(repo, remote):
    """
    Create a temporary branch (with a unique name).  When finished,
    delete the branch.
    """
    name = temp_branch_name(repo)
    try:
        git_cmd(repo, 'branch', '-t', name, remote)
        yield name
    finally:
        git_cmd(repo, 'branch', '-D', name)

@contextmanager
def stash_if_needed(repo):
    """
    Temporarily stash any changes.  When finished, stash pop.
    """
    stashed = False
    try:
        if repo.git.diff() != '':
            stashed = True
            git_cmd(repo, 'stash')
        yield
    finally:
        if stashed:
            git_cmd(repo, 'stash', 'pop')

@contextmanager
def checkout(repo, branch):
    """
    Temporarily checkout a git branch.  When finished, checkout the
    original branch again.
    """
    orig = repo.active_branch
    try:
        git_cmd(repo, 'checkout', branch)
        yield
    finally:
        git_cmd(repo, 'checkout', orig)

def fetch_needed(repo, remote_repo, remote_branch):
    """
    Do we already know about this remote branch?  If not, we should to
    try to fetch it.
    """
    for ref in repo.remote().refs:
        if ref.remote_name == remote_repo and ref.remote_head == remote_branch:
            return False
    return True

def get_revision(repo, rev):
    """
    Get the revision to push.  Returns a git.Commit object.

    If we are given the name of a revision, just convert it to a
    git.Commit object.

    If we are given a file, take the last commit that modified that
    file.
    """

    try:
        return repo.commit(rev)
    except BadObject:
        if os.path.exists(rev):
            fullpath = os.path.abspath(rev)
            gen = repo.iter_commits(paths=fullpath)
            try:
                return gen.next()
            except StopIteration:
                pass

        raise ValueError("Unknown file or commit: {0}".format(rev))

def cherry_push(repo, rev, remote_repo, remote_branch, do_pull=False):
    """
    Push a specific commit to a particular branch.  This function is
    the heart of the logic in this script.
    """

    print ("Pushing commit {0} to {1}:{2}\n\n{3}\n".
           format(rev, remote_repo, remote_branch, rev.message))

    with stash_if_needed(repo):
        # Make sure the remote branch exists so we can track it
        remote = '{0}/{1}'.format(remote_repo, remote_branch)
        if fetch_needed(repo, remote_repo, remote_branch):
            git_cmd(repo, 'fetch', remote_repo,
                    '{0}:remotes/{1}'.format(remote_branch, remote))

        # Create a unique temp branch
        with temp_branch(repo, remote) as branch_name:

            # Checkout the temp branch
            with checkout(repo, branch_name):
                git_cmd(repo, 'cherry-pick', rev)
                git_cmd(repo, 'pull', '--rebase')
                git_cmd(repo, 'prep')
                git_cmd(repo, 'push')

        # We only want to pull in the original active branch if we pushed
        # to the same branch that the active branch is tracking
        if do_pull:
            git_cmd(repo, 'pull', '--rebase')

##################################################################
# Functions related to pushing to the master branch
#

def get_tracking(repo):
    """
    Return the branch which is upstream of the currently active branch.

    Throws an exception if the HEAD is detached (there is no active
    branch) or the active branch is not a tracking branch.
    """
    # This will throw a TypeError if HEAD is detached
    tracking = repo.active_branch.tracking_branch()
    if tracking is None:
        raise AssertionError("Can't determine which branch to push to.  "
                             "Current branch is not tracking and no "
                             "upstream given")
    return tracking

def default_to_tracking(repo, remote_repo, remote_branch):
    """
    Return the remote repo and branch to use.  If either isn't
    specified, get the values from the branch that is being tracked by
    the repo's currently active branch.
    """

    if remote_repo is None or remote_branch is None:
        tracking = get_tracking(repo)
        if remote_repo is None:
            remote_repo = tracking.remote_name
        if remote_branch is None:
            if remote_repo != tracking.remote_name:
                raise AssertionError("Can't determine which branch of remote"
                                     " {0} to push to.  Current branch tracks"
                                     "{1}/{2}".format(remote_repo,
                                                      tracking.remote_name,
                                                      tracking.remote_head))
            remote_branch = tracking.remote_head
    return (remote_repo, remote_branch)

def push_to_master(repo, rev, remote_repo, remote_branch, force):
    """
    Select a particular command and push it to the remote 'master'.
    """
    (remote_repo, remote_branch) = default_to_tracking(
        repo, remote_repo, remote_branch)
    if not force and remote_branch != 'master':
        raise ValueError("Are you sure you want to push to branch {0}"
                         " instead of branch 'master'?  If so, use --force."
                         .format(remote_branch))
    cherry_push(repo, rev, remote_repo, remote_branch, do_pull=True)

##################################################################

if __name__ == "__main__":
    main()
