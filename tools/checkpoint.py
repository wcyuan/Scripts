#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -*- mode: python; eval: (no-pyformat-mode) -*-
"""
"""

# --------------------------------------------------------------------------- #

from __future__ import absolute_import, division, with_statement

import contextlib
import inspect
import logging
import optparse
import os
import tempfile

# --------------------------------------------------------------------------- #

logging.basicConfig(format="[%(asctime)s "
                    "%(funcName)s:%(lineno)s %(levelname)-5s] "
                    "%(message)s")

# --------------------------------------------------------------------------- #


def main():
  (opts, args) = getopts()
  checkpoint_tester(
    checkpoints=opts.checkpoints,
    filename=opts.filename,
    start_from=opts.start_from,
    last_checkpoint=opts.last_checkpoint,
    leave_file=opts.leave_file,
    predefine_checkpoints=opts.predefine_checkpoints,
    error_at=opts.error_at)

# --------------------------------------------------------------------------- #


def getopts():
  parser = optparse.OptionParser()
  parser.add_option("--verbose", action="store_true")
  parser.add_option("--log_level", help="The level to log at")
  parser.add_option("--filename",
                    help="The filename to store the last checkpoint in")
  parser.add_option("--checkpoints", help="The list of checkpoints",
                    action="append")
  parser.add_option("--error_at", help="Have an error at this checkpoint",
                    action="append")
  parser.add_option("--start_from",
                    help="Start from this checkpoint "
                    "(ignore the checkpoint file)")
  parser.add_option("--last_checkpoint",
                    help="Set the last checkpoint "
                    "(ignore the checkpoint file)")
  parser.add_option("--predefine_checkpoints", action="store_true")
  # parser.add_option("--no_write",
  #                   action="store_true",
  #                   help="Just print commands without running them")
  parser.add_option("--leave_file", action="store_true")
  (opts, args) = parser.parse_args()

  if opts.verbose:
    logat(logging.DEBUG)

  if opts.log_level:
    logat(opts.log_level)

  return (opts, args)


def logat(level):
  if isinstance(level, basestring):
    level = getattr(logging, level.upper())
  logging.getLogger().setLevel(level)
  logging.info("Setting log level to %s", level)

# --------------------------------------------------------------------------- #

def check_args(checkpoints, start_from, last_checkpoint, error_at):
  if start_from:
    if start_from not in checkpoints:
      logging.error(
          "Checkpoint to start from '%s' is not among "
          "the list of checkpoints: %s", start_from, checkpoints)

  if last_checkpoint:
    if last_checkpoint not in checkpoints:
      logging.error(
          "Checkpoint to start from '%s' is not among "
          "the list of checkpoints: %s", last_checkpoint, checkpoints)

  if error_at:
    invalid = [cp for cp in error_at if cp not in checkpoints]
    if invalid:
      logging.error(
          "Checkpoints to error_at %s are not among "
          "the list of checkpoints: %s", invalid, checkpoints)

def checkpoint_tester(checkpoints=None, filename=None, start_from=None,
                      last_checkpoint=None, leave_file=False,
                      predefine_checkpoints=False,
                      error_at=None, num_checkpoints=4):
  """
  >>> with tempfile.NamedTemporaryFile() as f:
  ...     checkpoint_tester(filename=f.name, leave_file=True)
  ...     checkpoint_tester(filename=f.name, leave_file=True)
  Entering Checkpoint:  cp0
  Exiting  Checkpoint:  cp0
  Entering Checkpoint:  cp1
  Exiting  Checkpoint:  cp1
  Entering Checkpoint:  cp2
  Exiting  Checkpoint:  cp2
  Entering Checkpoint:  cp3
  Exiting  Checkpoint:  cp3
  Entering Checkpoint:  cp0
  Exiting  Checkpoint:  cp0
  Entering Checkpoint:  cp1
  Exiting  Checkpoint:  cp1
  Entering Checkpoint:  cp2
  Exiting  Checkpoint:  cp2
  Entering Checkpoint:  cp3
  Exiting  Checkpoint:  cp3
  >>> with tempfile.NamedTemporaryFile() as f:
  ...     try:
  ...         checkpoint_tester(filename=f.name, error_at=["cp2"], leave_file=True)
  ...     except ValueError as e:
  ...         print e
  ...     checkpoint_tester(filename=f.name, leave_file=True)
  Entering Checkpoint:  cp0
  Exiting  Checkpoint:  cp0
  Entering Checkpoint:  cp1
  Exiting  Checkpoint:  cp1
  Entering Checkpoint:  cp2
  Raising an error at cp2
  Entering Checkpoint:  cp2
  Exiting  Checkpoint:  cp2
  Entering Checkpoint:  cp3
  Exiting  Checkpoint:  cp3
  """
  if not checkpoints:
    checkpoints = ["cp{0}".format(ii) for ii in range(num_checkpoints)]

  check_args(checkpoints, start_from, last_checkpoint, error_at)

  cp = Checkpoints(checkpoints=checkpoints if predefine_checkpoints else None,
                  filename=filename,
                  next_checkpoint=start_from,
                  last_checkpoint=last_checkpoint,
                  delete_file_when_finished=not leave_file)
  for cp_name in checkpoints:
    with cp.checkpoint(cp_name) as should_execute:
      if should_execute:
        print "Entering Checkpoint: ", cp_name
        if error_at and cp_name in error_at:
          raise ValueError("Raising an error at {0}".format(cp_name))
        print "Exiting  Checkpoint: ", cp_name
  if not predefine_checkpoints:
    cp.finished_all_checkpoints()

# --------------------------------------------------------------------------- #

class Checkpoints(object):
  """
  >>> cp = Checkpoints()
  >>> with cp.checkpoint("first") as should_execute:
  ...     should_execute
  True
  >>> with cp.checkpoint("second") as should_execute:
  ...     should_execute
  True
  >>> cp = Checkpoints(next_checkpoint="third")
  >>> with cp.checkpoint("first") as should_execute:
  ...     should_execute
  False
  >>> with cp.checkpoint("second") as should_execute:
  ...     should_execute
  False
  >>> with cp.checkpoint("third") as should_execute:
  ...     should_execute
  True
  >>> with cp.checkpoint("fourth") as should_execute:
  ...     should_execute
  True
  """

  import os
  import contextlib

  def __init__(self,
               checkpoints=None,
               filename=None,
               next_checkpoint=None,
               last_checkpoint=None,
               delete_file_when_finished=True):
    self.filename = filename
    self.last_checkpoint = None
    self.checkpoints = checkpoints
    self.delete_file_when_finished = delete_file_when_finished

    #
    # If checkpoints are not predefined:
    #   if last_checkpoint is defined and start_from is not:
    #     - we don't run anything until we see the last_checkpoint checkpoint
    #     - once we've seen that, we don't run it, but we'll run any
    #       new checkpoint we see
    #   if start_from is defined:
    #     - we don't run anything until we see the start_from checkpoint
    #     - once we've seen that, we run it
    #   In both cases:
    #     - when we exit a checkpoint that was not run,
    #       if it matches last_checkpoint, then we set
    #       seen_last_checkpoint to True
    #     - when we exit a checkpoint that was run,
    #       we set last_checkpoint to the new
    #       checkpoint and we unset next_checkpoint
    #     - when we set last_checkpoint, if we have a filename,
    #       we write the checkpoint to that filename
    #   next_checkpoint and last_checkpoint should never both be set,
    #   but if they are, next_checkpoint takes precedence.
    #
    # If checkpoints are predefined:
    #   - everything is the same except that we insist that all the checkpoints
    #     match what we've seen and we complain if things are out of order
    #
    self.last_checkpoint = None
    self.seen_last_checkpoint = False
    self.next_checkpoint = None

    if next_checkpoint:
      self._verify_checkpoint(next_checkpoint)
      self.next_checkpoint = next_checkpoint
    elif self.filename:
      checkpoint = self._read_file()
      if checkpoint:
        self._verify_checkpoint(checkpoint)
      self.last_checkpoint = checkpoint

  def _read_file(self):
    if not self.filename:
      return
    if not os.path.exists(self.filename):
      return
    with open(self.filename) as fd:
      return fd.read().rstrip()

  def _write_file(self, txt):
    if not self.filename:
      return
    with open(self.filename, "w") as fd:
      fd.write(txt)
      fd.write("\n")

  def _delete_file(self):
    if not self.filename:
      return
    os.unlink(self.filename)

  def _verify_checkpoint(self, name):
    if self.checkpoints:
      if name not in self.checkpoints:
        raise ValueError(
            "Checkpoint {0} not in predefined list of checkpoints: {1}".format(
                name, self.checkpoints))
    return name

  def _should_execute(self, name):
    if self.next_checkpoint:
      should_execute = name == self.next_checkpoint
    elif self.last_checkpoint:
      should_execute = self.seen_last_checkpoint
    else:
      should_execute = True
    logging.debug("Entering checkpoint '%s'.  Should execute = %s.  "
                  "Last checkpoint = %s, next_checkpoint = %s, "
                  "seen_last_checkpoint = %s", name, should_execute,
                  self.last_checkpoint, self.next_checkpoint,
                  self.seen_last_checkpoint)
    return should_execute

  def _post_execute(self, name, executed):
    if executed:
      self.next_checkpoint = None
      self.last_checkpoint = name
      self.seen_last_checkpoint = True
      if self.filename:
        if self.checkpoints and self.last_checkpoint == self.checkpoints[-1]:
          self.finished_all_checkpoints()
        else:
          self._write_file(self.last_checkpoint)
    else:
      if self.last_checkpoint == name:
        self.seen_last_checkpoint = True
    logging.debug("Exiting checkpoint '%s'.  Executed = %s.  "
                  "Last checkpoint = %s, next_checkpoint = %s, "
                  "seen_last_checkpoint = %s", name, executed,
                  self.last_checkpoint, self.next_checkpoint,
                  self.seen_last_checkpoint)

  @contextlib.contextmanager
  def checkpoint(self, name):
    self._verify_checkpoint(name)
    should_execute = self._should_execute(name)
    yield should_execute
    self._post_execute(name, should_execute)

  def finished_all_checkpoints(self):
    if self.delete_file_when_finished:
      self._delete_file()
    else:
      self._write_file("")

# --------------------------------------------------------------------------- #

# A total, nonportable hack: a context manager that can skip its body
# http://stackoverflow.com/questions/12594148/skipping-execution-of-with-block
# However, this is too hacky to use, it's only included here for reference.
class SkippableContext(object):
  import inspect
  def __init__(self, name=None, skip=False):
    """
    if skip = False, proceed as normal
    if skip = True, do not execute block
    """
    self.should_skip = skip
  def __enter__(self):
    if self.should_skip:
      # Do some magic
      sys.settrace(lambda *args, **keys: None)
      frame = inspect.currentframe(1)
      frame.f_trace = self.trace
  def trace(self, frame, event, arg):
    raise
  def __exit__(self, type, value, traceback):
    print 'Exiting context ...'
    return True

# --------------------------------------------------------------------------- #

if __name__ == "__main__":
  main()

# --------------------------------------------------------------------------- #
