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

    >>> parser = PassThroughOptionParser()
    >>> _ = parser.add_option('--test', action='store_true')
    >>> parser.disable_interspersed_args()

    # We don't recognize any options, so just pass them through
    >>> (opts, args) = parser.parse_args(['a', 'b', 'c'])
    >>> opts.test
    >>> args
    ['a', 'b', 'c']

    # Pass through '--' unchanged
    >>> (opts, args) = parser.parse_args(['a', 'b', '--', 'c'])
    >>> args
    ['a', 'b', '--', 'c']
    >>> (opts, args) = parser.parse_args(['a', 'b', '--', 'c', '--'])
    >>> args
    ['a', 'b', '--', 'c', '--']

    # We remove the leading '--' if it is the first argument
    >>> (opts, args) = parser.parse_args(['--', 'a', 'b', '--', 'c', '--'])
    >>> args
    ['a', 'b', '--', 'c', '--']


    # Consume the option we expected
    >>> (opts, args) = parser.parse_args(['--test', 'a', 'b', '--', 'c', '--'])
    >>> opts.test
    True
    >>> args
    ['a', 'b', '--', 'c', '--']

    >>> (opts, args) = parser.parse_args(['--test', '--', 'a', 'b', '--', 'c', '--'])
    >>> opts.test
    True
    >>> args
    ['a', 'b', '--', 'c', '--']

    >>> (opts, args) = parser.parse_args(['--', '--test', 'a', 'b', '--', 'c', '--'])
    >>> opts.test
    >>> args
    ['--test', 'a', 'b', '--', 'c', '--']

    """
    def _process_args(self, largs, rargs, values):
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

class FieldMixin(object):
    """
    This Mixin applies to classes that have a few key attributes that
    determine all the other behavior.  Those attributes have to be
    settable as keyword arguments in the __init__ function.  In that
    case, if you put the names of those attributes in _flds, then this
    Mixin will provide repr, cmp, and hash functions.

    """
    @property
    def _flds(self):
        raise NotImplementedError

    @staticmethod
    def _vals(obj):
        return tuple(getattr(obj, fld) for fld in obj._flds)

    def __repr__(self):
        """
        Must satisfy:
          obj == eval(repr(obj))
        for any obj
        """
        cn = self.__class__.__name__
        fmt = ('{cn}(' +
               ',\n{pd} '.join('{0} = {{self.{0}!r}}'.format(fld)
                               for fld in (self._flds)) +
               ')')
        return fmt.format(self=self, cn=cn, pd=' '*len(cn))

    def __cmp__(self, other):
        tcmp = cmp(type(self), type(other))
        if tcmp == 0:
            return cmp(self._vals(self), self._vals(other))
        else:
            return tcmp

    def __hash__(self):
        return hash(self._vals(self))

# --------------------------------------------------------------------------- #

