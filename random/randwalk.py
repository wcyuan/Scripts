#!/usr/bin/env python
"""
What's the expected number of steps in a one-dimensional random walk
with endpoints 0 and N, and equal probability of moving in either
direction, when the starting point is x.
"""

from __future__ import absolute_import, division, with_statement

from   optparse                 import OptionParser
from   logging                  import getLogger, DEBUG, info

import numpy

##################################################################

def main():
    """
    """
    opts,args = getopts()
    simulate(opts.n, opts.x, opts.steps, raw=opts.raw)

def getopts():
    """
    Parse the command-line options
    """
    parser = OptionParser()
    parser.add_option('-n',
                      type=int,
                      default=30,
                      help='The endpoint')
    parser.add_option('-x',
                      type=int,
                      default=10,
                      help='The starting point')
    parser.add_option('-t', '--steps', '--num_steps',
                      type=int,
                      help='The number of steps to simulate')
    parser.add_option('--raw',
                      action='store_true',
                      help='print number of paths without dividing by total')
    parser.add_option('--verbose',
                      action='store_true',
                      help='Turn on debug logging')
    opts,args = parser.parse_args()

    if opts.verbose:
        getLogger().setLevel(DEBUG)

    return (opts,args)

##################################################################

def output(a, raw=False, vert=False):
    print " ".join("%6.2f" % x for x in (a if raw else 100*a))

def simulate(n, x, t, raw=False):
    if t is None:
        t = 2*n*n

    info("Simulating {0} steps from 0 to {1} starting at {2}".
         format(t, n, x))

    stopr = numpy.zeros(t+1)
    stopl = numpy.zeros(t+1)

    a = numpy.zeros(n+1)
    a[x] = 1
    for step in range(t):
        output(a, raw=raw)
        stopl[step] = a[0]
        stopr[step] = a[n]
        a[0] = a[n] = 0
        right = numpy.roll(a, 1)
        left = numpy.roll(a, -1)
        a = right + left
        if not raw:
            a /= 2
    output(a, raw=raw)
    stopl[t] = a[0]
    stopr[t] = a[n]

    print
    print "{0} steps".format(t)

    for i in range(t+1):
        print ("%6s %6.2f %6.2f %6.2f" %
               (i, 100*stopl[i], 100*stopr[i], 100*(stopl[i]+stopr[i])))
    print sum((stopl+stopr) * numpy.arange(t+1))
    print x*(n-x)
    return stopl+stopr

##################################################################

if __name__ == "__main__":
    main()
