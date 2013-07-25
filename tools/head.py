#!/usr/bin/env python
#
'''
Contains the head function, which is useful for grabbing part of a sequence

Run this module as a script to run doctests
'''

import itertools

# --------------------------------------------------------------------

def indices(seq, *args):
    """
    Print a part of a sequence

    # No args, defaults to first 20 elements
    >>> head(range(100))
    (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19)

    # One arg is like [:A]
    >>> head(range(100), 10)
    (0, 1, 2, 3, 4, 5, 6, 7, 8, 9)

    # Two args, is like [A:B]
    >>> head(range(100), 3, 10)
    (3, 4, 5, 6, 7, 8, 9)

    # Three args, is like [A:B:C]
    >>> head(range(100), 3, 10, 2)
    (3, 5, 7, 9)

    # One negative args, is like [-A:]
    >>> head(range(100), -3)
    (97, 98, 99)

    # Two args, if any are negative, is like [-A:-B]
    >>> head(range(100), -10, -5)
    (90, 91, 92, 93, 94)

    # works for generators, too
    >>> head(i for i in xrange(100))
    (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19)
    >>> head((i for i in xrange(100)), 10)
    (0, 1, 2, 3, 4, 5, 6, 7, 8, 9)
    >>> head((i for i in xrange(100)), 3, 10)
    (3, 4, 5, 6, 7, 8, 9)
    >>> head((i for i in xrange(100)), 3, 10, 2)
    (3, 5, 7, 9)

    # For generators, we don't know the length before hand, so the
    # negative args don't really work
    >>> head((i for i in xrange(100)), -3)
    (0, 1, 2)
    >>> head((i for i in xrange(100)), -10, -5)
    (0, 1, 2, 3, 4)
    """
    #
    # Parse arguments as, roughly:
    #   seq, [start], end=20, [step]
    # Same arguments as islice, except that end defaults to 20
    #
    # Basically it's the same as
    #   seq, start=0, end=20, step=1
    # except that if you only provide two positional arguments, they
    # are seq and end, not seq and start.
    #
    start = None
    end = 20
    step = None
    if len(args) == 1:
        if args[0] < 0:
            start = args[0]
            end = None
        else:
            end = args[0]
    elif len(args) == 2:
        (start, end) = args
    elif len(args) == 3:
        (start, end, step) = args
    elif len(args) > 3:
        raise ValueError("Too many arguments for head: {0}".format(args))

    try:
        length = len(seq)
    except:
        length = max(abs(x) for x in (start, end) if x is not None)

    return slice(start, end, step).indices(length)


def head(seq, *args, **kwargs):
    (start, end, step) = indices(seq, *args)
    return tuple(itertools.islice(seq, start, end, step, **kwargs))

# --------------------------------------------------------------------

if __name__ == "__main__":
    import doctest
    doctest.testmod()

# --------------------------------------------------------------------
