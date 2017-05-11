#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -*- mode: python; eval: (no-pyformat-mode) -*-
"""

With help from:
http://stackoverflow.com/questions/375427/non-blocking-read-on-a-subprocess-pipe-in-python
http://stackoverflow.com/questions/12270645/can-you-make-a-python-subprocess-output-stdout-and-stderr-as-usual-but-also-cap

  # Start the wrapper
  >>> wrap = shell_wrapper.Wrap(command)

  # Send the process a command
  >>> wrap.write("my command")

  # Get output
  >>> wrap.get_output()

  # The last string that was output
  >>> wrap.stdout[-1]

"""

# --------------------------------------------------------------------------- #

from __future__ import absolute_import, division, with_statement

import logging
import optparse
import select
import subprocess
import sys
import time
from threading  import Thread
try:
  from Queue import Queue, Empty
except ImportError:
  from queue import Queue, Empty  # python 3.x

ON_POSIX = 'posix' in sys.builtin_module_names

# --------------------------------------------------------------------------- #


logging.basicConfig(format="[%(asctime)s "
                    "%(funcName)s:%(lineno)s %(levelname)-5s] "
                    "%(message)s")

# --------------------------------------------------------------------------- #


def main():
  (opts, args) = getopts()

# --------------------------------------------------------------------------- #


def getopts():
  parser = optparse.OptionParser()
  parser.add_option("--verbose", action="store_true")
  parser.add_option("--log_level", help="The level to log at")
  parser.add_option("--no_write", "--dry_run",
                    action="store_true",
                    help="Just print commands without running them")
  (opts, args) = parser.parse_args()
  if opts.verbose:
    logat(logging.DEBUG)
  if opts.log_level:
    logat(opts.log_level)
  if opts.no_write:
    Runner.NO_WRITE = True
  return (opts, args)


def logat(level):
  if isinstance(level, basestring):
    level = getattr(logging, level.upper())
  logging.getLogger().setLevel(level)
  logging.info("Setting log level to %s", level)


def enqueue_output(out, queue):
  for line in iter(out.readline, b''):
    queue.put(line)
  out.close()


class Wrap(object):
  """A class to wrap shells.

  All output will be both printed to stdout/stderr and saved.  Unless
  suppress=True, in which case the output will only be saved, it won't
  be printed.
  """
  def __init__(self, cmd, suppress=False, no_write=False, proc=None):
    self.cmd = cmd
    self.stdout = []
    self.stderr = []
    self.suppress = suppress
    self.proc = proc
    self.no_write = no_write
    self._sysfds = {"stderr": sys.stderr, "stdout": sys.stdout}
    self._queue = {}
    self._thread = {}


  def __repr__(self):
    return "{0}(cmd={1!r}, no_write={2!r}, proc={3!r})".format(
        self.__class__.__name__,
        self.cmd,
        self.no_write,
        self.proc)


  def start(self):
    if self.proc:
      return
    if isinstance(self.cmd, basestring):
      strcmd = self.cmd
    else:
      strcmd = "{0} ({1})".format(self.cmd, " ".join(cmd))
    if self.no_write:
      logging.info("NO WRITE: %s", strcmd)
      return
    logging.info("Starting cmd: %s", strcmd)
    self.proc = subprocess.Popen(
        self.cmd,
        shell=isinstance(self.cmd, basestring),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        bufsize=1, close_fds=ON_POSIX)
    self._make_thread("stdout", self.proc.stdout)
    self._make_thread("stderr", self.proc.stderr)
    return self


  def _make_thread(self, name, fd):
    self._queue[name] = Queue()
    self._thread[name] = Thread(
        target=enqueue_output, args=(fd, self._queue[name]))
    self._thread[name].daemon = True
    self._thread[name].start()
    return self._thread[name]


  def get_output(self, timeout=3):
    if not self.proc:
      self.start()
    has_output = True
    data = {}
    while has_output or timeout > 0:
      has_output = False
      for name in self._queue:
        # read line without blocking
        try:
          line = self._queue[name].get_nowait() # or q.get(timeout=.1)
        except Empty:
          pass
        else:
          has_output = True
          if not self.suppress:
            if name in self._sysfds:
              self._sysfds[name].write(line)
            else:
              logging.error("Invalid fd %s", name)
              sys.stderr.write(line)
          data.setdefault(name, []).append(line)
      if timeout > 0:
        timeout -= 1
        if not has_output:
          logging.info("No output, sleeping for 1 second")
          time.sleep(1)
    if data:
      for name in data:
        if name == "stderr":
          arr = self.stderr
        elif name == "stdout":
          arr = self.stdout
        else:
          arr = self.other
        arr.append("".join(data[name]))


  def write(self, data, timeout=3):
    if not self.proc:
      self.start()
    self.proc.stdin.write(data.strip())
    self.proc.stdin.write("\n")
    return self.get_output(timeout=timeout)

# --------------------------------------------------------------------------- #

if __name__ == "__main__":
  main()

# --------------------------------------------------------------------------- #
