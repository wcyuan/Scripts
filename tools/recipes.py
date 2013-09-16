'''
A place to store useful python recipes
'''

# --------------------------------------------------------------------------- #

# http://stackoverflow.com/questions/1885161/
# how-can-i-get-optparses-optionparser-to-ignore-invalid-options

from optparse import (OptionParser,BadOptionError,AmbiguousOptionError)

class PassThroughOptionParser(OptionParser):
    """
    An unknown option pass-through implementation of OptionParser.

    When unknown arguments are encountered, bundle with largs and try again,
    until rargs is depleted.

    sys.exit(status) will still be called if a known argument is passed
    incorrectly (e.g. missing arguments or bad argument types, etc.)
    """
    def _process_args(self, largs, rargs, values):
        while rargs:
            try:
                OptionParser._process_args(self,largs,rargs,values)
            except (BadOptionError,AmbiguousOptionError), e:
                largs.append(e.opt_str)

def pass_through_example():
    preparser = PassThroughOptionParser()
    preparser.add_option('--full', action='store_true',
                         help='an added flag argument')
    (options, args) = preparser.parse_args()

    # Now pass the rest of the arguments to the original parser
    parser = OptionParser()
    parser.add_option('--orig', action='store_true',
                         help='the original argument')
    (opts, args) = parser.parse_args(args)



# --------------------------------------------------------------------------- #

# http://stackoverflow.com/questions/5136611/
# capture-stdout-from-a-script-in-python

import sys
import StringIO

def save_stdout(func):
    old_stdout = sys.stdout
    new_stdout = StringIO.StringIO()
    sys.stdout = new_stdout
    func()
    sys.stdout = old_stdout
    return new_stdout.getvalue()

def save_stdout_example():
    def myfunc():
        """ A function that has lots of output """
        for i in xrange(100):
            print 'abc' * 100

    # capture the output
    output = save_stdout(lambda : myfunc())
    # only print the first 100 characters
    print output[:100]

# --------------------------------------------------------------------------- #
