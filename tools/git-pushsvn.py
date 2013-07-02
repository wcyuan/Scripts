#!/usr/local/bin/python
#
"""
A simple helper script to pull changes through to multiple dependent branches.

Currently, this does no error handling, so it will fail if there are
merge conflicts, or uncommitted changes, etc.
"""

from __future__ import absolute_import, division, with_statement

import argparse
import contextlib
import logging
import os
import subprocess
import git

# ------------------------------------------------------------------

def main():
    args = getopt()

    repo = git.Repo(args.repo)

    revision = (repo.head.commit
                if args.revision is None
                else get_revision(args.revision))

    with stash_if_needed(repo, leave=args.leave):
        with checkout(repo, 'master'):
            git_cmd(repo, 'cherry-pick', revision)
            git_cmd(repo, 'svn', 'dcommit')
            git_cmd(repo, 'big-update')

# ------------------------------------------------------------------

def getopt():
    parser = argparse.ArgumentParser()
    parser.add_argument('--no_write',
                        action='store_true',
                        help='Just print commands without running them')
    parser.add_argument('--verbose',
                        action='store_true',
                        help='Turn on verbose logging')
    parser.add_argument('--repo',
                        help='the repo to use')
    parser.add_argument('--leave',
                        action='store_true',
                        help='the repo to use')
    parser.add_argument('revision',
                        nargs='?',
                        help='the revision to push')
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    if args.no_write:
        Runner.NO_WRITE = True

    return args

# ------------------------------------------------------------------

def __git_cmd(repo, always, cmd, *args):
    '''
    Run a git command.  If it's a command that should run, even in
    no_write mode, then always should be True.

    If always is not True, and no_write is True, we just print the
    command to run without running it.

    Otherwise we print the command and then run it.  We print the
    command in a form that the user could copy and paste and run on
    the command line.
    '''
    cmdline = 'git %s %s' % (
        cmd, ' '.join(str(a) for a in args))
    if not always and Runner.NO_WRITE:
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

# ------------------------------------------------------------------

@contextlib.contextmanager
def checkout(repo, branch, leave=False):
    """
    Temporarily checkout a git branch.  When finished, checkout the
    original branch again.
    """
    orig = repo.active_branch
    git_cmd(repo, 'checkout', branch)
    exception = None
    try:
        yield
    except Exception as e:
        exception = e
    finally:
        if exception is None or not leave:
            try:
                git_cmd(repo, 'reset', '--merge')
                git_cmd(repo, 'checkout', orig)
            except Exception as cleanup_e:
                if exception is None:
                    raise cleanup_e
                else:
                    print "Error while trying to clean up"
                    print cleanup_e
        if exception is not None:
            raise exception

@contextlib.contextmanager
def stash_if_needed(repo, leave=False):
    """
    Temporarily stash any changes.  When finished, stash pop.
    """
    stashed = False
    if git_cmd_always(repo, 'diff') != '':
        stashed = True
        git_cmd(repo, 'stash')
    exception = None
    try:
        yield
    except Exception as e:
        exception = e
    finally:
        if exception is None or not leave:
            if stashed:
                try:
                    git_cmd(repo, 'stash', 'pop')
                except Exception as cleanup_e:
                    if exception is None:
                        raise cleanup_e
                    else:
                        print "Error while trying to clean up"
                        print cleanup_e
        if exception is not None:
            raise exception

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


# ------------------------------------------------------------------

class Runner(object):
    NO_WRITE = False

    @classmethod
    def run(cls, cmd, always=False, die_on_error=True):
        '''
        If die_on_error is False, then if the command exits with a
        non-zero exit code, we will log a warning, but we won't throw
        an exception.  However, if the command doesn't even exist, or
        if Popen is called with invalid arguments, then we will still
        throw an exception.
        '''
        if cls.NO_WRITE and not always:
            print "NO WRITE: {0}".format(cmd)
            return

        print "Running:  {0}".format(cmd)
        process = subprocess.Popen(cmd.split(),
                                   stdout=subprocess.PIPE)
        stdout = process.communicate()[0]
        if process.returncode != 0:
            if die_on_error:
                raise RuntimeError("Failure running {0}".format(cmd))
            else:
                logging.warning("Error running {0}".format(cmd))
        logging.info("Command {0} finished with return code {1}".
                     format(cmd, process.returncode))
        return stdout

# ------------------------------------------------------------------

if __name__ == '__main__':
    main()
