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
        print "{0} = {1}".format(expr, expr.value)

def getopts():
    parser = optparse.OptionParser()
    parser.add_option('--verbose',       action='store_true')
    parser.add_option('--log_level')
    parser.add_option('--generate',      action='store_true')
    parser.add_option('--num_vals',      type=int)
    parser.add_option('--target', '-t',  type=int)
    parser.add_option('--min_target',    type=int, default=DEFAULT_MIN_TARGET)
    parser.add_option('--max_target',    type=int, default=DEFAULT_MAX_TARGET)
    parser.add_option('--num_large',     type=int, default=DEFAULT_NUM_LARGE)
    parser.add_option('--large_numbers', default=DEFAULT_LARGE_NUMBERS)
    parser.add_option('--integer',       action='store_true',
                      help='Requires that every intermediate step '
                      'in the calculation produces an integer')
    parser.add_option('--positive',      action='store_true',
                      help='Requires that every intermediate step in '
                      'the calculation produces a positive number')

    (opts, args) = parser.parse_args()

    if opts.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    if opts.log_level is not None:
        level = getattr(logging, opts.log_level.upper())
        logging.getLogger().setLevel(level)
        logging.info("Setting log level to %s", level)

    if opts.num_vals is None:
        opts.num_vals = len(args)
        if opts.num_vals == 0:
            opts.num_vals = DEFAULT_NUM_VALS

    opts.large_numbers = opts.large_numbers.split(',')

    if opts.integer:
        Operators.DIV = Operators.SDIV

    if opts.positive:
        Expression.POSITIVE_ONLY = True

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
    given = [int(g) for g in given]
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

class ExpressionError(Exception):
    pass

class Expression(object):
    POSITIVE_ONLY = False

    def __init__(self, value):
        self._value = value

    @property
    def value(self):
        if self._value is None:
            value = self.compute_value()
            if self.POSITIVE_ONLY and value < 0:
                raise ExpressionError("Negative value")
            self._value = value
        return self._value

    def compute_value(self):
        raise NotImplementedError

    def __str__(self):
        return str(self.value)

    @property
    def exception(self):
        try:
            self.value
            return False
        except ZeroDivisionError:
            return True
        except ExpressionError:
            return True

    @property
    def integer(self):
        return int(self.value) == self.value

    @property
    def negative(self):
        return self.value < 0

class Value(Expression):
    def __init__(self, value):
        super(Value, self).__init__(value)

    def __repr__(self):
        return "Value({0})".format(self.value)

    def __eq__(self, other):
        return type(self) == type(other) and self.value == other.value

    def __hash__(self):
        return hash(self.value)

class BiExpr(Expression):
    CACHE = {}

    def __init__(self, operator, left, right):
        super(BiExpr, self).__init__(None)
        self.operator = operator
        self.left  = left
        self.right = right

    def compute_value(self):
        return self.operator(self.left.value, self.right.value)

    def __str__(self):
        return '({0} {1} {2})'.format(self.left, self.operator, self.right)

    def __eq__(self, other):
        return ((self.operator, self.left, self.right) ==
                (other.operator, other.left, other.right))

    def __hash__(self):
        return hash((self.operator, self.left, self.right))

    @classmethod
    def get_expr(cls, operator, left, right):
        key = (operator, left, right)
        if key not in cls.CACHE:
            cls.CACHE[key] = BiExpr(operator, left, right)
        return cls.CACHE[key]


class Operator(object):
    def __init__(self, func, string, commutative=False):
        self.func = func
        self.string = string
        self.commutative = commutative
    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)
    def __str__(self):
        return self.string
    def __eq__(self, other):
        return self.string == other.string
    def __hash__(self):
        return hash(self.string)

def fpeq(a, b, epsilon=1e-6):
    """
    Floating point equality
    """
    return abs(a - b) < epsilon

def intdiv(a, b):
    v = a / b
    if fpeq(v, round(v)):
        return round(v)
    raise ExpressionError("{0} is not a multiple of {1}".format(a, b))

def try_round(v):
    return round(v) if fpeq(v, round(v)) else v

class Operators(object):
    ADD  = Operator(operator.add, '+', commutative=True)
    SUB  = Operator(operator.sub, '-')
    MUL  = Operator(operator.mul, '*', commutative=True)
    DIV  = Operator(operator.truediv, '/')

    # Throws an error if the value isn't an integer
    SDIV = Operator(intdiv, '/')

    @classmethod
    def all(cls):
        return (cls.ADD, cls.SUB, cls.MUL, cls.DIV)

def get_subsets(lst, max_size=None):
    """
    >>> [s for s in get_subsets(())]
    [()]
    >>> [s for s in get_subsets((1,))]
    [(), (1,)]
    >>> [s for s in get_subsets((1, 2))]
    [(), (1,), (2,), (1, 2)]
    >>> [s for s in get_subsets((1, 2, 3))]
    [(), (1,), (2,), (1, 2), (3,), (1, 3), (2, 3), (1, 2, 3)]
    >>> [s for s in get_subsets((1, 2, 3), max_size=2)]
    [(), (1,), (2,), (1, 2), (3,), (1, 3), (2, 3)]
    >>> [s for s in get_subsets((1, 1))]
    [(), (1,), (1, 1)]
    >>> [s for s in get_subsets((1, 1, 2))]
    [(), (1,), (1, 1), (2,), (1, 2), (1, 1, 2)]
    >>> [s for s in get_subsets((1, 1, 2, 2))]
    [(), (1,), (1, 1), (2,), (1, 2), (1, 1, 2), (2, 2), (1, 2, 2), (1, 1, 2, 2)]
    """
    if len(lst) <= 0:
        yield lst
        return
    seen = set()
    for subset in get_subsets(lst[1:], max_size=max_size):
        sset = tuple(sorted(subset))
        if sset not in seen:
            yield subset
            seen.add(sset)
        if max_size is None or len(subset) + 1 <= max_size:
            new = (lst[0],) + subset
            sset = tuple(sorted((new)))
            if sset not in seen:
                yield new
                seen.add(sset)

def get_partitions(lst):
    """
    >>> [p for p in get_partitions([])]
    []
    >>> [p for p in get_partitions([1])]
    []
    >>> [p for p in get_partitions(range(2))]
    [([0], [1])]
    >>> [p for p in get_partitions(range(3))]
    [([0], [1, 2]), ([0, 1], [2])]
    >>> [p for p in get_partitions(range(4))]
    [([0], [1, 2, 3]), ([0, 1], [2, 3]), ([0, 1, 2], [3])]
    """
    for ii in xrange(1, len(lst)):
        yield lst[:ii], lst[ii:]

def permutations(lst):
    """
    >>> import itertools
    >>> [p for p in permutations(())]
    [()]
    >>> [p for p in permutations((1,))]
    [(1,)]
    >>> [p for p in permutations((1, 2))]
    [(1, 2), (2, 1)]
    >>> [p for p in permutations((1, 2, 3))]
    [(1, 2, 3), (1, 3, 2), (2, 1, 3), (2, 3, 1), (3, 1, 2), (3, 2, 1)]
    >>> [p for p in permutations((1, 1))]
    [(1, 1)]
    >>> [p for p in permutations((1, 1, 2))]
    [(1, 1, 2), (1, 2, 1), (2, 1, 1)]
    >>> comp = lambda lst: set(p for p in permutations(lst)) == set(p for p in itertools.permutations(lst))
    >>> comp(tuple(range(3)))
    True
    >>> comp(tuple(range(4)))
    True
    >>> comp(tuple(range(5)))
    True
    """
    if len(lst) == 0:
        yield lst
        return
    seen = set()
    for (ii, elt) in enumerate(lst):
        if elt in seen:
            continue
        seen.add(elt)
        for perm in permutations(lst[:ii] + lst[ii+1:]):
            yield (elt,) + perm

def get_splits(vals, all_orders=False, all_subsets=False):
    """
    >>> [s for s in get_splits((), all_orders=True, all_subsets=True)]
    []
    >>> [s for s in get_splits(tuple(range(1)), all_orders=True, all_subsets=True)]
    []
    >>> [s for s in get_splits(tuple(range(2)), all_orders=True, all_subsets=True)]
    [((0,), (1,)), ((1,), (0,))]
    >>> [s for s in get_splits(tuple(range(3)), all_orders=True, all_subsets=True)]
    [((0,), (1,)), ((1,), (0,)), ((0,), (2,)), ((2,), (0,)), ((1,), (2,)), ((2,), (1,)), ((0,), (1, 2)), ((0, 1), (2,)), ((0,), (2, 1)), ((0, 2), (1,)), ((1,), (0, 2)), ((1, 0), (2,)), ((1,), (2, 0)), ((1, 2), (0,)), ((2,), (0, 1)), ((2, 0), (1,)), ((2,), (1, 0)), ((2, 1), (0,))]
    """
    import itertools

    if all_subsets:
        subsets = (s for s in get_subsets(vals)
                   if len(s) > 0)
    else:
        subsets = (vals,)

    if all_orders:
        perms = set(p
                    for s in subsets
                    for p in permutations(s))
    else:
        perms = subsets

    return itertools.chain.from_iterable(
        get_partitions(p) for p in perms)

def all_expressions(vals, all_orders=False, all_subsets=False):
    """
    @param vals: a list of Value or Expr objects.
    """
    if len(vals) == 1:
        yield vals[0]
        return

    if all_orders and all_subsets:
        logging.debug("Vals: {0}".format(vals))

    splits = get_splits(
        vals, all_orders=all_orders, all_subsets=all_subsets)

    for (lpart, rpart) in splits:
        if all_orders and all_subsets:
            logging.debug("Doing split {0} v {1}".format(lpart, rpart))
        for left in all_expressions(lpart):
            if left.exception:
                continue
            for right in all_expressions(rpart):
                if right.exception:
                    continue
                for op in Operators.all():
                    expr = BiExpr.get_expr(op, left, right)
                    if not expr.exception:
                        yield expr

                    # if not op.commutative:
                    #     expr = BiExpr.get_expr(op, right, left)
                    #     if not expr.exception:
                    #         yield expr

def countdown(vals, target):
    vals = tuple(Value(v) for v in vals)
    closest = []
    best = None
    tries = 0
    tried = set()
    for expr in all_expressions(vals, all_orders=True, all_subsets=True):
        if str(expr) in tried:
            logging.error("Tried the same expression twice: {0}".format(expr))
            continue
        tried.add(str(expr))
        tries += 1
        value = try_round(expr.value)
        distance = abs(target - value)
        logging.debug("Trying {0} = {1}, abs({2} - {1}) = {3}".format(
            expr, value, target, distance))
        if len(closest) == 0:
            closest.append(expr)
            best = distance
        elif distance < best:
            logging.info(
                "Found {0} = {1}, distance = abs({2} - {1}) = {3} < {4}".format(
                    expr, value, target, distance, best))
            closest = [expr]
            best = distance
        elif distance == best:
            logging.info(
                "Found {0} = {1}, distance = abs({2} - {1}) = {3} = {4}".format(
                    expr, value, target, distance, best))
            closest.append(expr)
        if distance == 0:
            yield expr
        if tries % 1000000 == 0:
            logging.info("{0} expressions tried so far".format(tries))
    logging.info("Tried {0} expressions".format(tries))
    if best != 0:
        for c in closest:
            yield expr


# --------------------------------------------------------------------------- #

if __name__ == "__main__":
    main()

# --------------------------------------------------------------------------- #
