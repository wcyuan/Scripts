#!/usr/bin/env python
"""
git-cherry-push.py [--master | --release | --both] [--force] [revision|file]

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

By default it will push the commit to the master branch.  There is a
--release option to push to the current release branch, and ae --both
option to push first to the master branch, then the release branch.

In order to use --release, your remote repository must have separate
branches for "released" code, and the branch names should have the
form rel_yyyymmdd.  Also, there must be a shared clone of the release
branch at /some/path/<release_tag>.  Finally, there must be a link to
the latest release at /testbed/github/release/<type>.

In --master mode, we require that the currently active branch tracks
the master branch (and that that branch is called 'master').  If you
run with --force, then we will push to whatever branch the active
branch tracks, even if it isn't called 'master'.

In --master mode, after pushing the commit, we will do a pull on the
currently active branch in the local repository.  We assume that the
current branch is tracking the same branch that you pushed to, so
you'll want the current branch to be updated to reflect the change you
just pushed.

In --release mode, we will push to the current release branch, whose
name we get from the shared release clone in
/testbed/github/release.  You can override the release branch name
with the --upstream option.  If you do that, the branch name must look
like rel_<yyyymmdd> or else the script will complain.  To allow
different branch names, use the --force option.

In --release mode, we create a new branch that tracks the current
remote release branch.  That means that we will fetch the remote
release branch so we can track it.  This could add a remote branch to
your local repository.

In --release mode, we require that the hash of the commit being pushed
can already be found somewhere in the history of the master branch.
To push a commit that isn't already in the master branch, use --force.
Note that a commit's hash encodes its history.  When you cherry-pick a
commit, that changes its history change and so its hash will change.
Say you have a local commit whose hash is 2b68d73.  Then you
cherry-push it to the master branch, and its hash changes to 78432905.
If you then try to cherry-push that commit to the release branch, you
need to cherry-push the new hash 78432905, not 2b68d73, because
78432905 can be found in the master branch's history but 2b68d73
cannot.

In --release mode, after pushing the commit, we will do a pull in the
shared clone.  We will not attempt to do a desmake in the shared clone
or to dist the change, we leave that for the user.  However, we will
print out some brief instructions for how to do the desmake and dist.


Created by: Conan Yuan (yuanc), 20120830
"""
#
#

from __future__ import absolute_import, division, with_statement

from   contextlib               import contextmanager
from   datetime                 import datetime
from   operator                 import itemgetter
from   optparse                 import OptionParser

# For GitPython documentation, try
# https://groups.google.com/forum/?fromgroups#!forum/git-python
from   git                      import Repo, BadObject

import os
import re

##################################################################

# Path to the shared clones of the release trees for various
# repositories.
RELEASE_PATH = '/testbed/github/release/'

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

    check_rev_in_master = True
    if opts.master:
        push_to_master(repo, rev, opts.remote, opts.upstream, opts.force,
                       opts.leave)
        check_rev_in_master = False

    if opts.release:
        push_to_release(repo, rev, opts.remote, opts.upstream, opts.force,
                        opts.date, opts.release_date,
                        check_rev_in_master=check_rev_in_master,
                        leave=opts.leave)


def getopts():
    """
    Parse the command-line options
    """
    parser = OptionParser()

    parser.add_option('--no_write',
                      action='store_true',
                      help="Print the commands to run without running them")
    parser.add_option('--release',
                      action='store_true',
                      help='Commit to the release branch')
    parser.add_option('--master', '--trunk', '--proj', '--qa',
                      action='store_true',
                      help='Commit to the master branch')
    parser.add_option('--both', '--all',
                      action='store_true',
                      help='Commit to both the master and release branches')
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
    parser.add_option('--release_date',
                      help='The date of the release branch to push to',
                      type='int')
    parser.add_option('--date',
                      help="Today's date",
                      type='int')
    parser.add_option('--leave',
                      action='store_true',
                      help="Don't clean up on conflict")

    opts, args = parser.parse_args()

    if len(args) > 1:
        raise ValueError("Too many arguments")

    if opts.no_write:
        global FLAG_NO_WRITE
        FLAG_NO_WRITE = True

    # Allow the user to specify the remote repo and branch together as
    # remote/branch
    if opts.remote is None:
        if opts.upstream is not None:
            if '/' in opts.upstream:
                (opts.remote, opts.upstream) = opts.upstream.split('/', 2)

    if opts.date is None:
        opts.date = int(datetime.now().strftime("%Y%m%d"))

    #
    # no options means just do the master branch
    # -master    means just do the master branch
    # -release   means just do the release branch
    # -both      means do both branches
    #
    if opts.both:
        opts.master  = True
        opts.release = True

    if not opts.master and not opts.release:
        opts.master = True

    return (opts, args)

##################################################################
# Functions for doing a cherry-pick and a push (given the branch to
# push to)
#

def __git_cmd(repo, always, cmd, *args):
    """
    Run a git command.  If it's a command that should run, even in
    no_write mode, then always should be True.

    If always is not True, and no_write is True, we just print the
    command to run without running it.

    Otherwise we print the command and then run it.  We print the
    command in a form that the user could copy and paste and run on
    the command line.
    """
    cmdline = 'git %s %s' % (
        cmd, ' '.join(str(a) for a in args))
    if not always and FLAG_NO_WRITE:
        print "Would run: " + cmdline
    else:
        print "Running  : " + cmdline

        # On the command line you have to run "cherry-pick", but in
        # the git package, the command is cherry_pick.  So replace
        # hyphens with underscores.
        cmd = cmd.replace('-', '_')
        return getattr(repo.git, cmd)(*args)

def git_cmd(repo, cmd, *args):
    '''
    Run a git command.  If no_write is True, then just print the
    command to run without running it.
    '''
    return __git_cmd(repo, False, cmd, *args)

def git_cmd_always(repo, cmd, *args):
    '''
    Run a git command, even if no_write is True.  Print the command
    before running it.
    '''
    return __git_cmd(repo, True, cmd, *args)

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

def handle_exception(exception, leave=False):
    if leave:
        raise(exception)
    else:
        print("[cherry-push] Failed due to error %s" % exception)
        print("[cherry-push] Cleaning up temp branch.")
        print("[cherry-push] To be left in the middle of the "
              "conflict, use the --leave option.")

@contextmanager
def temp_branch(repo, remote, leave=False):
    """
    Create a temporary branch (with a unique name).  When finished,
    delete the branch.
    """
    name = temp_branch_name(repo)
    git_cmd(repo, 'branch', '-t', name, remote)
    try:
        yield name
    except Exception as e:
        handle_exception(e, leave=leave)
    git_cmd(repo, 'branch', '-D', name)

@contextmanager
def stash_if_needed(repo, leave=False):
    """
    Temporarily stash any changes.  When finished, stash pop.
    """
    stashed = False
    if git_cmd_always(repo, 'diff') != '':
        stashed = True
        git_cmd(repo, 'stash')
    try:
        yield
    except Exception as e:
        handle_exception(e, leave=leave)
    if stashed:
        git_cmd(repo, 'stash', 'pop')

@contextmanager
def checkout(repo, branch, leave=False):
    """
    Temporarily checkout a git branch.  When finished, checkout the
    original branch again.
    """
    orig = repo.active_branch
    git_cmd(repo, 'checkout', branch)
    try:
        yield
    except Exception as e:
        handle_exception(e, leave=leave)
    git_cmd(repo, 'reset', '--merge')
    git_cmd(repo, 'checkout', orig)

def remote_branch_exists(repo, remote_repo, remote_branch):
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

def cherry_push(repo, rev, remote_repo, remote_branch, do_pull=False,
                leave=False):
    """
    Push a specific commit to a particular branch.  This function is
    the heart of the logic in this script.
    """

    print ("Pushing commit {0} to {1}:{2}\n\n{3}\n".
           format(rev, remote_repo, remote_branch, rev.message))

    with stash_if_needed(repo, leave):
        # Make sure the remote branch exists so we can track it
        remote = '{0}/{1}'.format(remote_repo, remote_branch)
        if remote_branch_exists(repo, remote_repo, remote_branch):
            git_cmd(repo, 'fetch', remote_repo,
                    '{0}:remotes/{1}'.format(remote_branch, remote))

        # Create a unique temp branch
        with temp_branch(repo, remote, leave) as branch_name:

            # Checkout the temp branch
            with checkout(repo, branch_name, leave):
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

def default_to_tracking(repo, remote_repo, remote_branch=None):
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

def push_to_master(repo, rev, remote_repo, remote_branch, force, leave=False):
    """
    Select a particular command and push it to the remote 'master'.
    """
    (remote_repo, remote_branch) = default_to_tracking(
        repo, remote_repo, remote_branch)
    if not force and remote_branch != 'master':
        raise ValueError("Are you sure you want to push to branch {0}"
                         " instead of branch 'master'?  If so, use --force."
                         .format(remote_branch))
    cherry_push(repo, rev, remote_repo, remote_branch, do_pull=True,
                leave=leave)

##################################################################
# Functions related to pushing to the release branch
#

def get_repository_type(repo, remote_repo):
    """
    Returns the name of the type of tree this is.  We get this from
    the url for the remote repository.  We need this name in order to
    find the shared clone.
    """

    # If the user didn't specify a remote, use the remote being
    # tracked by the current branch.  If the current branch isn't
    # tracking, throw an error.
    if remote_repo is None:
        tracking = get_tracking(repo)
        if remote_repo is None:
            remote_repo = tracking.remote_name

    remote_url = repo.config_reader().get_value('remote "{0}"'.
                                                format(remote_repo), 'url')
    return os.path.basename(remote_url)

def get_release_tree(repo_type, release_branch=None):
    """
    Get the shared clone of the release branch

    If release_branch is None, return the default release tree (e.g.,
    /testbed/github/release/<repo_type>).  If release_branch is given,
    return the release tree specific to that branch, which we get by
    following the link from /testbed/github/release/<repo_type>, then
    replacing the last directory with the release_branch given.

    If there is no shared clone (the path doesn't exist), return None.
    """
    rel_tree = RELEASE_PATH + repo_type
    if release_branch is not None:
        if not os.path.islink(rel_tree):
            return None
        release_path = os.readlink(rel_tree).rstrip('/')
        release_root = os.path.dirname(release_path)
        rel_tree = release_root + '/' + release_branch
    return rel_tree

def get_release_branch_date(string, pattern):
    """
    Given the name of a release branch, and a regexp for parsing
    release branches, where the first matching group is the date,
    return the date of the release branch, as an integer.

    If the release branch name doesn't match the regexp, return None.
    """
    matches = re.match(pattern, string)
    if matches is None:
        return None
    return int(matches.group(1))

def get_release_branch(repo, repo_type, remote_repo, release_branch_pattern,
                       today, release_date=None):
    """
    Get the current release branch.

    Use the filename that the release clone link is pointing to.
    We could also get the release clone's active branch, which
    should have the same result.

    If the shared clone of the release branch isn't found, then we try
    to get the release branch name by listing all branches and picking
    the one that looks like rel_YYYYMMDD, with the latest date.

    """
    rel_tree = get_release_tree(repo_type)
    if rel_tree is not None and os.path.exists(rel_tree):
        if not os.path.islink(rel_tree):
            raise ValueError("Unsupported repository {0}, {1} exists "
                             "but is not a symlink.".
                             format(repo_type, rel_tree))
        release_path = os.readlink(rel_tree)
        release_branch = os.path.basename(release_path)

        # or:
        # release_branch = git.Repo(rel_tree).active_branch

    else:
        # get the release branch from the names of the branches on the
        # remote repo
        release_branch = None

        # Fetch all branches for this remote to make sure we have them
        # all.  This will modify the state of the repository, even in
        # no_write mode.  But in a way that hopefully no one will mind.
        git_cmd_always(repo, 'fetch', remote_repo)

        # filter out any branches that are for a different remote
        remote_branches = ((ref.remote_head,
                            get_release_branch_date(ref.remote_head,
                                                    release_branch_pattern))
                           for ref in repo.remote().refs
                           if ref.remote_name == remote_repo)

        # filter out any branches that don't fit the pattern or are
        # for future dates.

        remote_branches = [(branch, date)
                           for (branch, date) in remote_branches
                           if date is not None and date <= today]

        if len(remote_branches) == 0:
            raise ValueError("Unsupported or unknown repository {0} (type {1}"
                             ", no release branches fit pattern {2}.".format(
                             repo, repo_type, release_branch_pattern))

        if release_date is not None:
            for (branch, date) in remote_branches:
                if date == release_date:
                    release_branch = branch
                    break
            else:
                raise ValueError("No release branch for date {0}".
                                 format(release_date))
        else:
            # sort descending by branch date
            remote_branches = sorted(remote_branches,
                                     key=itemgetter(1),
                                     reverse=True)

            if remote_branches[0][1] == today:
                if len(remote_branches) > 1:
                    raise ValueError("Today is a release date.  Use the "
                                     "--release_date option to specify "
                                     "whether this commit should go to the "
                                     "previous release branch %s or the new "
                                     "one %s" % (remote_branches[1][0],
                                                 remote_branches[0][0]))

            release_branch = remote_branches[0][0]

    return release_branch

def do_git_pull(git_root):
    """
    Do a pull on the shared release clone to keep it up-to-date.
    """
    if FLAG_NO_WRITE:
        print "Would Run: cd " + git_root
    else:
        # We don't actually need to do a chdir, we just need to pass
        # that path to the git.Repo contructor.  However, we still
        # print a message saying that we chdir, so users can follow
        # along with what we are doing.  That way they could have run
        # the commands we printed to get the same effect.
        print "Running  : cd " + git_root
    git_cmd(Repo(git_root), 'pull', '--rebase')

def ensure_rev_in_master(repo, rev, remote_repo):
    """
    Make sure that this revision is in the master branch of the remote
    repository before you push the revision to the release branch.  If
    the revision isn't there, throw an error.

    Note that if you have a commit in a branch with a bunch of other
    commits, then you cherry-pick that into a separate branch, that
    commit's hash will change.  That's what happens if you cherry-push
    a branch to the master.  That means that when you cherry-push a
    revision, the hash will change.

    That means that if you cherry-push a commit to the master branch,
    then use that same hash to cherry-push to the release branch, this
    check will fail because the commit's hash will have changed when
    it was cherry-picked to push into the master branch.  So if you
    want to push a revision to the master branch, then to the release
    branch, you have to get the new hash.
    """
    matches = git_cmd_always(repo, 'branch', '-r', '--contains', rev)
    in_master = "^\s*{0}/master$".format(remote_repo)
    for match in matches.split("\n"):
        if re.match(in_master, match) is not None:
            return True
    raise ValueError("Commit {0} has not been pushed to the master branch, "
                     "are you sure you want to push it to the release branch?"
                     "  If so, use --force.".format(rev))

def push_to_release(repo, rev, remote_repo, remote_branch,
                    force, today, release_date=None, check_rev_in_master=True,
                    leave=False):
    """
    Push a specific commit to the current release branch
    """
    repo_type = get_repository_type(repo, remote_repo)


    # If the remote_repo wasn't given, default it to the repo of the
    # branch being tracked by the active branch.
    remote_repo = default_to_tracking(repo, remote_repo)[0]

    release_branch_pattern = '^rel_(\d+)$'

    if remote_branch is None:
        remote_branch = get_release_branch(repo, repo_type, remote_repo,
                                           release_branch_pattern, today,
                                           release_date)

    if not force:
        if get_release_branch_date(remote_branch,
                                   release_branch_pattern) is None:
            raise ValueError("Remote branch {0} doesn't look like "
                             "rel_YYYYMMDD.  Use --force to continue".
                             format(remote_branch))

        if check_rev_in_master:
            ensure_rev_in_master(repo, rev, remote_repo)

    cherry_push(repo, rev, remote_repo, remote_branch, leave=leave)
    rel_tree = get_release_tree(repo_type, remote_branch)
    if rel_tree is None or not os.path.exists(rel_tree):
        print("No shared release clone to update!  "
              "Can't find {0}".format(rel_tree))
        return

    do_git_pull(rel_tree)

    # It would be nice if we could give more information about how to
    # make the tree and publish changes, but that's not related to git.
    #
    # Instead, we just print the location of the shared release.

    # rev.stats.files gives a dict whose keys are the files that were
    # modified in this commit.
    files_in_commit = rev.stats.files.keys()

    print
    print('# Run "make" in the release tree.')
    print '# For example:'
    print '#   cd {0}/{1}...'.format(
        rel_tree,
        os.path.dirname(files_in_commit[0]))
    print '#   make'
    print

##################################################################

if __name__ == "__main__":
    main()
