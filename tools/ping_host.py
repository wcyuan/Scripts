#!/usr/bin/env python
'''
A wrapper around ping
'''

# --------------------------------------------------------------------------- #

from __future__ import absolute_import, division, with_statement

import logging
import optparse
import subprocess

DEFAULT_COUNT = 1
DEFAULT_TIMEOUT = 10

# --------------------------------------------------------------------------- #

def main():
    (opts, hosts) = getopts()
    unreachable = set(host
                      for host in hosts
                      if not ping(host, count=opts.count, timeout=opts.timeout))
    if unreachable:
        print "Can't reach hosts: {0}".format(', '.join(unreachable))

def getopts():
    parser = optparse.OptionParser()
    parser.add_option('--count', type=int, default=DEFAULT_COUNT)
    parser.add_option('--timeout', type=int, default=DEFAULT_TIMEOUT)
    parser.add_option('--verbose',  action='store_true')
    (opts, args) = parser.parse_args()
    if opts.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    return (opts, args)

# --------------------------------------------------------------------------- #

def ping(host, count=DEFAULT_COUNT, timeout=DEFAULT_TIMEOUT):
    cmd = ['ping', '-c', str(count), '-W', str(timeout), host]
    logging.debug("Running %s", cmd)
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    (stdout, _) = proc.communicate()
    logging.debug("Output from '%s': %s", cmd, stdout)
    return proc.returncode == 0

# --------------------------------------------------------------------------- #

if __name__ == "__main__":
    main()

