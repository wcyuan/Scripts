#!/usr/bin/env python
"""
"""

# --------------------------------------------------------------------------- #

from __future__ import absolute_import, division, with_statement

import logging
import optparse
import subprocess

logging.basicConfig(format='[%(asctime)s '
                    '%(funcName)s:%(lineno)s %(levelname)-5s] '
                    '%(message)s')

# --------------------------------------------------------------------------- #

def main():
    (opts, args) = getopts()

def getopts():
    parser = optparse.OptionParser()
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

class Runner(object):
    """A class to run commands. """

    NO_WRITE = False

    @classmethod
    def run(cls, cmd, always=False, die_on_error=True, warn_on_error=True,
            capture_stdout=True):
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
      Otherwise, if capture_stdout is False, we return True iff returncode == 0

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
        logging.info("NO WRITE: %s", strcmd)
        return

    logging.info("Running:  %s", strcmd)
    if capture_stdout:
        stdout_opt = subprocess.PIPE
    else:
        stdout_opt = None
    process = subprocess.Popen(cmd,
                               shell=isinstance(cmd, basestring),
                               stdout=stdout_opt)
    stdout = process.communicate()[0]
    if process.returncode != 0:
        if die_on_error:
            raise RuntimeError("Failure running {0}".format(cmd))
        elif warn_on_error:
            logging.warning("Error running %s", cmd)
        else:
            logging.debug("Error running %s", cmd)
    logging.info("Command %s finished with return code %s",
                 cmd, process.returncode)
    if capture_stdout:
        return stdout
    else:
        return process.returncode == 0

# --------------------------------------------------------------------------- #

if __name__ == "__main__":
    main()

# --------------------------------------------------------------------------- #
