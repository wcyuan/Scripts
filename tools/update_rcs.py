#!/usr/bin/env python
#
"""
 update_rcs.py <filename> <command>

Update a file under rcs control

1. Checkout the file
2. Run the command, overwriting the file with the command's output
3. If the command fails, restore the original file
4. If the file hasn't changed, restore the original file
5. If the file has changed, check it in
"""
from __future__ import absolute_import, division, with_statement

import argparse
import logging
import subprocess
import sys

# --------------------------------------------------------------------

logging.basicConfig(format='%(asctime)-15s %(levelname)-5s %(message)s')

def main():
    """
    The main function.  Most of the logic is in process_args
    """
    args = getopts()
    Runner.run('co -l -f {0}'.format(args.file))
    Runner.run('{0} > {1}'.format(' '.join(args.command), args.file),
               shell=True)
    Runner.run("ci -m'Update by {0}' -u {1}".format(' '.join(sys.argv),
                                                     args.file),
               shell=True)

# --------------------------------------------------------------------

def getopts():
    """
    Parse the command line
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--verbose',
                        action='store_true',
                        help='turn on debug logging')
    parser.add_argument('--no_write',
                        action='store_true',
                        help='Just print commands without running them')
    parser.add_argument('file',
                        help='the file to generate')
    parser.add_argument('command',
                        nargs='+',
                        help='the command to generate the file')
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    if args.no_write:
        Runner.NO_WRITE = True

    return args

# --------------------------------------------------------------------

class Runner(object):
    NO_WRITE = False

    @classmethod
    def run(cls, cmd, always=False, die_on_error=True, shell=False):
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
        if shell:
            process = subprocess.Popen(cmd,
                                       stdout=subprocess.PIPE,
                                       shell=True)
        else:
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


# --------------------------------------------------------------------

if __name__ == "__main__":
    main()

