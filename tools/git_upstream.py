#!/usr/bin/env python
"""A script to push/pull across git repositories.

"""

# --------------------------------------------------------------------------- #

from __future__ import absolute_import, division, with_statement

import contextlib
import logging
import optparse
import subprocess

logging.basicConfig(format='[%(asctime)s '
                    '%(funcName)s:%(lineno)s %(levelname)-5s] '
                    '%(message)s')

# --------------------------------------------------------------------------- #

def main():
  (opts, args) = getopts()

  if opts.pull:
    stream_pull(opts.num)

  if opts.push:
    stream_push(args, num=opts.num)
    stream_pull(opts.num)

def getopts():
  parser = optparse.OptionParser()
  parser.add_option('--pull', action='store_true')
  parser.add_option('--push', action='store_true')
  parser.add_option('-n', '--num', type=int)
  parser.add_option('--verbose',  action='store_true')
  parser.add_option('--log_level',
                    help="The level to log at")
  parser.add_option('--no_write', action='store_true',
                    help='Just print commands without running them')
  (opts, args) = parser.parse_args()

  if opts.verbose:
    logat(logging.DEBUG)

  if opts.log_level is not None:
    logat(opts.log_level)

  if opts.no_write:
    Runner.NO_WRITE = True

  return (opts, args)

def logat(level):
  if isinstance(level, basestring):
    level = getattr(logging, level.upper())
  logging.getLogger().setLevel(level)
  logging.info("Setting log level to %s", level)

# --------------------------------------------------------------------------- #

def stream_pull(num=None):
  current_branch = get_current_branch()
  trail = get_upstream_trail()
  if num is not None:
    trail = trail[-num:]
  if not trail:
    return
  trail = trail + (current_branch,)
  with stash_if_needed():
    for (upstream, branch) in zip(trail[:-1], trail[1:]):
      with checkout(branch):
        Runner.run(["git", "pull", "--rebase"])

def stream_push(revs, num=None, leave=False):
  if not revs:
    revs = [get_revision_hash()]
  else:
    revs = [get_revision_hash(rev) for rev in revs]

  trail = get_upstream_trail()
  if num is not None:
    trail = trail[-num:]
  if not trail:
    return

  target = trail[0]
  if not is_branch_remote(target):
    # local branch to local branch -- just do a cherry pick
    with stash_if_needed(leave=leave):
      with checkout(target, leave=leave):
        for rev in revs:
          print "Cherry-picking commit {0} to {1}\n\n{2}".format(
              rev, target, get_revision_message())
        for rev in revs:
          Runner.run(["git", "cherry-pick", rev])
  else:
    # local branch to remote branch -- create a temp branch with just
    # the desired changes and push that.
    with stash_if_needed(leave=leave):
      with temp_branch(target, leave=leave) as branch_name:
        with checkout(target, leave=leave):
          for rev in revs:
            print "Cherry-picking commit {0} to {1}\n\n{2}".format(
                rev, target, get_revision_message(rev))
          for rev in revs:
            Runner.run(["git", "cherry-pick", rev])
            Runner.run(["git", "pull", "--rebase"])
            Runner.run(["git", "push"])

# --------------------------------------------------------------------------- #

def handle_exception(exception, leave=False):
    if leave:
        raise(exception)
    else:
        print("[cherry-push] Failed due to error %s" % exception)
        print("[cherry-push] Cleaning up temp branch.")
        print("[cherry-push] To be left in the middle of the "
              "conflict, use the --leave option.")

def get_current_branch():
  return Runner.run(["git", "symbolic-ref", "--short", "HEAD"],
                    always=True, die_on_error=False).rstrip()

def is_branch_remote(branch):
  return "/" in branch

def needs_stash():
  return not Runner.run(["git", "diff", "--quiet", "HEAD"],
                        always=True, die_on_error=False, warn_on_error=False,
                        capture_stdout=False)

def get_upstream_branch(branch=None):
  (stdout, stderr, returncode) = Runner.run(
      ["git", "rev-parse", "--abbrev-ref",
       "{0}@{{upstream}}".format("" if branch is None else branch)],
      always=True, die_on_error=False, warn_on_error=False,
      return_output_and_returncode=True)
  if returncode == 0:
    return stdout.rstrip()
  else:
    return None

def get_upstream_trail(branch=None):
  upstream = get_upstream_branch(branch)
  if upstream is None:
    return ()
  if is_branch_remote(upstream):
    return (upstream,)
  else:
    trail = get_upstream_trail(branch=upstream)
    return trail + (upstream,)

@contextlib.contextmanager
def checkout(branch, leave=False):
  current_branch = get_current_branch()
  if current_branch == branch:
    yield
  else:
    Runner.run(["git", "checkout", branch])
    try:
      yield
    except Exception as e:
      handle_exception(e, leave=leave)
    Runner.run(["git", "reset", "--merge"])
    Runner.run(["git", "checkout", current_branch])

@contextlib.contextmanager
def stash_if_needed(leave=False):
  """
  Temporarily stash any changes.  When finished, stash pop.
  """
  stashed = False
  if needs_stash():
    stashed = True
    Runner.run(["git", "stash"])
  try:
    yield
  except Exception as e:
    handle_exception(e, leave=leave)
  if stashed:
    Runner.run(["git", "stash", "pop"])

def get_revision_hash(rev=None):
  """Get the hash of a revision

  rev can be anything that git log understands, including a filename
  (in which case we'll return the last committed change to that file)
  """
  cmd = ["git", "log", "--pretty=format:%H", "-n", "1"]
  if rev is not None:
    cmd.append(rev)
  return Runner.run(cmd, always=True).rstrip()

def get_revision_message(rev):
  return Runner.run(["git", "log", "-n", "1", rev], always=True).rstrip()

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

def temp_branch_name():
  """
  Returns a name which is not currently being used as a branch, so
  that we can safely create a new temporary branch with this name.
  """
  branches = get_local_branch_names()
  number = 0
  while True:
    temp = 'temp%d' % number
    if temp not in branches:
      return temp
    number += 1

def get_local_branch_names():
  branches = Runner.run(["git", "branch", "-l"], always=True)
  branches = branches.rstrip().split("\n")
  branches = [branch[2:].strip() if branch.startswith("* ") else branch.strip()
              for branch in branches]
  return branches

@contextlib.contextmanager
def temp_branch(remote, leave=False):
  """
  Create a temporary branch (with a unique name).  When finished,
  delete the branch.
  """
  name = temp_branch_name()
  Runner.run(["git", "branch", "-t", name, remote])
  try:
    yield name
  except Exception as e:
    handle_exception(e, leave=leave)
  Runner.run(["git", "branch", "-D", name])

# --------------------------------------------------------------------------- #

class Runner(object):
  """A class to run commands.

  """
  NO_WRITE = False

  @classmethod
  def run(cls, cmd, always=False, die_on_error=True, warn_on_error=True,
          capture_stdout=True, return_output_and_returncode=False):
    """Run the command.

    Args:

      cmd: the command to run.  Should be a string or a list of strings.

      always: If True, we will run even if no_write is true.  False by
      default.

      die_on_error: If False, then if the command exits with a
      non-zero exit code, we will log a warning, but we won't throw an
      exception.  True by default.

      However, if the command doesn't even exist, or if Popen is
      called with invalid arguments, then we will still throw an
      exception.

      warn_on_error: If the command fails and die_on_error is False,
      then we will either log a warning (if warn_on_error is True)
      or a debug message (if warn_on_error is False)

      capture_stdout: If true, this function will return the stdout.
      That means the stdout won't appear on the terminal.

    Returns:
      In NO_WRITE mode, we always return None.
      Otherwise, if capture_stdout is True, we return the command's stdout.
      Otherwise, if capture_stdout is False, we return the returncode == 0.

    Raises:
      RuntimeError: if the command fails and die_on_error is True.
      Can throw other errors if the command doesn't exist or if
      Popen is called with invalid arguments.

    """
    if isinstance(cmd, basestring):
      strcmd = cmd
    else:
      strcmd = "{0} ({1})".format(cmd, " ".join(cmd))

    if cls.NO_WRITE and not always:
      print "NO WRITE: ", strcmd
      return

    if always:
      logging.info("Running:  %s", strcmd)
    else:
      print "Running:  ", strcmd
    if capture_stdout:
      stdout_opt = subprocess.PIPE
      stderr_opt = subprocess.PIPE
    else:
      stdout_opt = None
      stderr_opt = None
    process = subprocess.Popen(cmd,
                               shell=isinstance(cmd, basestring),
                               stdout=stdout_opt,
                               stderr=stderr_opt)
    (stdout, stderr) = process.communicate()
    if process.returncode != 0:
      if die_on_error:
        raise RuntimeError("Failure running {0} ({1})".format(cmd, stderr))
      elif warn_on_error:
        logging.warning("Error running %s, (%s)", cmd, stderr)
      else:
        logging.debug("Error running %s, (%s)", cmd, stderr)
    logging.info("Command %s finished with return code %s",
                 cmd, process.returncode)
    if return_output_and_returncode:
      return (stdout, stderr, process.returncode)
    elif capture_stdout:
      return stdout
    else:
      return process.returncode == 0

# --------------------------------------------------------------------------- #

if __name__ == "__main__":
    main()

# --------------------------------------------------------------------------- #
