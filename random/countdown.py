#!/usr/bin/env python
"""
http://en.wikipedia.org/wiki/Countdown_%28game_show%29#Numbers_round

Given 6 integers, and a target integer, combine the 6 integers using
only the 4 basic arithmetic operations (+,-,*,/) to come as close as
possible to the target.

You don't have to use all 6 integers.  A number can be used as many
times as it appears.

In the game show, the target number is a random three digit number.
The 6 integers are drawn from two sets.  The set of large integers has
four numbers: (25, 50, 75, 100) (in some episodes this was changed to
(12, 37, 62, 87)).  The set of small integers had 20 numbers: the
numbers 1..10 twice.  The contestant could say how many of each set he
would like (e.g. 4 large and 2 small, which of course would give him
all the large numbers)

The game show further stipulates that every step of the calculation
must result in positive integers.

I'm not sure if the game show also requires that you apply each
operation one step at a time (i.e., a "left-most" parenthesization)

One example, using 3, 6, 25, 50, 75, 100, get to 952

((100 + 6) * 3 * 75 - 50) / 25 =  106 * 9 - 2 = 952

"""

# --------------------------------------------------------------------------- #

from __future__ import absolute_import, division, with_statement

import logging
import optparse
import operator

logging.basicConfig(format='[%(asctime)s '
                    '%(funcName)s:%(lineno)s %(levelname)-5s] '
                    '%(message)s')

# --------------------------------------------------------------------------- #

DEFAULT_NUM_VALS = 6
DEFAULT_MIN_TARGET = 100
DEFAULT_MAX_TARGET = 999
DEFAULT_NUM_LARGE = 4
DEFAULT_LARGE_NUMBERS = '25,50,75,100'

# --------------------------------------------------------------------------- #

def main():
    (opts, args) = getopts()
    (vals, target) = generate(
        opts.num_vals,
        target=opts.target,
        given=args,
        min_target=opts.min_target,
        max_target=opts.max_target,
        num_large=opts.num_large,
        large_numbers=opts.large_numbers)
    logging.info("Target: {0}, Vals: {1}".format(target, vals))
    for expr in countdown(vals, target):
        print expr

def getopts():
    parser = optparse.OptionParser()
    parser.add_option('--verbose',       action='store_true')
    parser.add_option('--generate',      action='store_true')
    parser.add_option('--num_vals',      type=int, default=6)
    parser.add_option('--target',        type=int)
    parser.add_option('--min_target',    type=int, default=100)
    parser.add_option('--max_target',    type=int, default=999)
    parser.add_option('--num_large',     type=int, default=DEFAULT_NUM_LARGE)
    parser.add_option('--large_numbers', default=DEFAULT_LARGE_NUMBERS)
    (opts, args) = parser.parse_args()
    if opts.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    opts.large_numbers = opts.large_numbers.split(',')

    return (opts, args)

# --------------------------------------------------------------------------- #

def sample_without_replacement(n, vals):
    if n > len(vals):
        raise ValueError("Can't choose {0} values from {1}".format(n, vals))
    import random
    copy = list(vals)
    retvals = []
    for _ in xrange(n):
        idx = random.randrange(0, len(copy))
        retvals.append(copy[idx])
        copy = copy[:idx] + copy[idx+1:]
    return retvals

def generate(num_vals=DEFAULT_NUM_VALS,
             target=None,
             given=None,
             min_target=DEFAULT_MIN_TARGET,
             max_target=DEFAULT_MAX_TARGET,
             num_large=DEFAULT_NUM_LARGE,
             large_numbers=None):
    import random

    # choose the target
    if target is None:
        target = random.randint(min_target, max_target)

    # choose the values
    if given is None:
        given = []
    if len(given) > num_vals:
        vals = given[:num_vals]
    else:
        vals = given
        if large_numbers is None:
            large_numbers = DEFAULT_LARGE_NUMBERS.split(',')
        large_numbers = [int(l) for l in large_numbers]
        vals.extend(
            sample_without_replacement(
                min(num_vals - len(vals), num_large), large_numbers))
        if num_vals > len(vals):
            vals.extend(sample_without_replacement(
                num_vals - len(vals), range(1, 11) * 2))
    return vals, target

# --------------------------------------------------------------------------- #

class Value(object):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return str(self.value)

class Expr(object):
    def __init__(self, operator, left, right):
        self.operator = operator
        self.left  = left
        self.right = right
        self._value = None

    @property
    def value(self):
        if self._value is None:
            self._value = self.operator(self.left.value, self.right.value)
        return self._value

    def __str__(self):
        return '({0} {1} {2})'.format(self.left, self.operator, self.right)

class Operator(object):
    def __init__(self, func, string):
        self.func = func
        self.string = string
    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)
    def __str__(self):
        return self.string

opadd = Operator(operator.add, '+')
opsub = Operator(operator.sub, '-')
opmul = Operator(operator.mul, '*')
opdiv = Operator(operator.div, '/')

def all_expressions(vals):
    """
    @param vals: a list of Value or Expr objects.
    """
    if len(vals) == 1:
        yield vals[0]
        return
    for ii in xrange(len(vals)-1):
        for left in all_expressions(vals[:ii+1]):
            try:
                if int(left.value) != left.value:
                    continue
            except ZeroDivisionError:
                continue
            for right in all_expressions(vals[ii+1:]):
                try:
                    if int(right.value) != right.value:
                        continue
                except ZeroDivisionError:
                    continue
                yield Expr(opadd, left, right)
                yield Expr(opsub, left, right)
                yield Expr(opsub, right, left)
                yield Expr(opmul, left, right)
                if right.value != 0:
                    yield Expr(opdiv, left, right)
                if left.value != 0:
                    yield Expr(opdiv, right, left)

def countdown(vals, target):
    vals = [Value(v) for v in vals]
    closest = []
    for expr in all_expressions(vals):
        if len(closest) == 0:
            closest.append(expr)
        elif abs(target - expr.value) < abs(target - closest[0].value):
            closest = [expr]
        elif abs(target - expr.value) == abs(target - closest[0].value):
            closest.append(expr)
    return closest


# --------------------------------------------------------------------------- #

if __name__ == "__main__":
    main()

# --------------------------------------------------------------------------- #
