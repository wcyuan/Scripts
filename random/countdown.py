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

Other examples:

Use 1, 3, 7, 10, 25, 50 to get 765

http://www.4nums.com/game/difficulties/

Compare to haskell version:
http://www.cs.nott.ac.uk/~gmh/countdown2.hs

"""

# --------------------------------------------------------------------------- #

from __future__ import absolute_import, division, with_statement

import logging
import optparse
import operator

from threading  import Thread

try:
    from Queue import Queue, Empty
except ImportError:
    from queue import Queue, Empty  # python 3.x

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
    print "Target: {0}, Vals: {1}".format(target, vals)

    (_, queue) = run_in_thread(("{0} = {1}".format(expr, expr.value)
                                for expr in countdown(
                                        vals, target,
                                        all_orders=(not opts.in_order),
                                        all_subsets=(not opts.use_all))))

    raw_input("Press Enter to See Solutions: ")
    while True:
        try:
            line = queue.get()
            print line
        except Empty:
            break

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
    parser.add_option('--in_order',      action='store_true',
                      help="The numbers must be used in order "
                      "in the expression")
    parser.add_option('--use_all',       action='store_true',
                      help="All the given numbers must be used "
                      "in the expression")
    parser.add_option('--integer',       action='store_true',
                      help='Requires that every intermediate step '
                      'in the calculation produces an integer')
    parser.add_option('--positive',      action='store_true',
                      help='Requires that every intermediate step in '
                      'the calculation produces a positive number')
    parser.add_option('--prune',         action='store_true',
                      help='prunes out some solutions '
                      'if shorter solutions exist')

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
        Operators.DIV = Operators.IDIV

    if opts.positive:
        Expression.POSITIVE_ONLY = True

    # This reduces the number of expressions we try, so we don't try
    # both a + b and b + a
    Operators.ADD = Operators.ASADD
    Operators.MUL = Operators.ASMUL

    if opts.prune:
        # This avoids any solution where we multiply or divide by an
        # expression that is 1
        Operators.MUL = Operators.SMUL
        Operators.ADD = Operators.SADD
        if opts.integer:
            Operators.DIV = Operators.SIDIV

    return (opts, args)

# --------------------------------------------------------------------------- #

def run_in_thread(gen):
    """
    Mostly stolen from
    http://stackoverflow.com/questions/375427/non-blocking-read-on-a-subprocess-pipe-in-python
    """
    def enqueue_output(gen, queue):
        for line in gen:
            queue.put(line)

    queue = Queue()
    t = Thread(target=enqueue_output, args=(gen, queue))
    t.daemon = True
    t.start()

    return (t, queue)

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
    USE_CACHE = False
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
        if cls.USE_CACHE:
            key = (operator, left, right)
            if key not in cls.CACHE:
                cls.CACHE[key] = BiExpr(operator, left, right)
            return cls.CACHE[key]
        else:
            return BiExpr(operator, left, right)


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
    if a % b != 0:
        raise ExpressionError("{0} is not a multiple of {1}".format(a, b))
    return operator.div(a, b)

def strictdiv(a, b):
    if a % b != 0 or b == 1:
        raise ExpressionError("{0} is not a multiple of {1}".format(a, b))
    return operator.div(a, b)

def asymadd(a, b):
    if a < b:
        raise ExpressionError("Optimization: only add bigger to smaller")
    return a + b

def asymmul(a, b):
    if a < b:
        raise ExpressionError("Optimization: only multiply bigger to smaller")
    return a * b

def strictmul(a, b):
    if a < b or a == 1 or b == 1:
        raise ExpressionError("Optimization: only multiply bigger to smaller")
    return a * b

def strictadd(a, b):
    if a < b or a == 0 or b == 0:
        raise ExpressionError("Optimization: only add bigger to smaller")
    return a + b

def try_round(v):
    return int(round(v)) if fpeq(v, round(v)) else v

class Operators(object):
    ADD  = Operator(operator.add, '+', commutative=True)
    SUB  = Operator(operator.sub, '-')
    MUL  = Operator(operator.mul, '*', commutative=True)
    DIV  = Operator(operator.truediv, '/')

    # Throws an error if the value isn't an integer
    IDIV = Operator(intdiv, '/')

    # Throws an error if the second number is bigger
    ASADD = Operator(asymadd, '+')
    ASMUL = Operator(asymmul, '*')

    # Throws an error if one of the arguments is the identity
    SADD  = Operator(strictadd, '+')
    SMUL  = Operator(strictmul, '*')
    SIDIV = Operator(strictdiv, '/')

    @classmethod
    def all(cls):
        return (cls.ADD, cls.SUB, cls.MUL, cls.DIV)

def get_subsets(lst, max_size=None, avoid_dups=False):
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
    >>> [s for s in get_subsets((1, 1), avoid_dups=True)]
    [(), (1,), (1, 1)]
    >>> [s for s in get_subsets((1, 1, 2), avoid_dups=True)]
    [(), (1,), (1, 1), (2,), (1, 2), (1, 1, 2)]
    >>> [s for s in get_subsets((1, 1, 2, 2), avoid_dups=True)]
    [(), (1,), (1, 1), (2,), (1, 2), (1, 1, 2), (2, 2), (1, 2, 2), (1, 1, 2, 2)]
    """
    if len(lst) <= 0:
        yield lst
        return
    seen = set()
    for subset in get_subsets(lst[1:], max_size=max_size,
                              avoid_dups=avoid_dups):
        if avoid_dups:
            sset = tuple(sorted(subset))
        if not avoid_dups or sset not in seen:
            yield subset
        if avoid_dups:
            seen.add(sset)
        if max_size is None or len(subset) + 1 <= max_size:
            new = (lst[0],) + subset
            if avoid_dups:
                sset = tuple(sorted((new)))
            if not avoid_dups or sset not in seen:
                yield new
            if avoid_dups:
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

def permutations(lst, avoid_dups=False):
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
    >>> [p for p in permutations((1, 1), avoid_dups=True)]
    [(1, 1)]
    >>> [p for p in permutations((1, 1, 2), avoid_dups=True)]
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
        if avoid_dups:
            if elt in seen:
                continue
            else:
                seen.add(elt)
        for perm in permutations(lst[:ii] + lst[ii+1:], avoid_dups=avoid_dups):
            yield (elt,) + perm

def get_splits(vals, all_orders=False, all_subsets=False, avoid_dups=True):
    """
    >>> [s for s in get_splits((), all_orders=True, all_subsets=True)]
    []
    >>> [s for s in get_splits(tuple(range(1)), all_orders=True, all_subsets=True)]
    []
    >>> [s for s in get_splits(tuple(range(2)), all_orders=True, all_subsets=True)]
    [((0,), (1,)), ((1,), (0,))]
    >>> sorted(s for s in get_splits(tuple(range(3)), all_orders=True, all_subsets=True, avoid_dups=True))
    [((0,), (1,)), ((0,), (1, 2)), ((0,), (2,)), ((0,), (2, 1)), ((0, 1), (2,)), ((0, 2), (1,)), ((1,), (0,)), ((1,), (0, 2)), ((1,), (2,)), ((1,), (2, 0)), ((1, 0), (2,)), ((1, 2), (0,)), ((2,), (0,)), ((2,), (0, 1)), ((2,), (1,)), ((2,), (1, 0)), ((2, 0), (1,)), ((2, 1), (0,))]

    """
    import itertools

    if all_subsets:
        subsets = (s for s in get_subsets(vals)
                   if len(s) > 0)
    else:
        subsets = (vals,)

    if all_orders:
        perms = (p
                 for s in subsets
                 for p in permutations(s, avoid_dups=avoid_dups))
        if avoid_dups:
            perms = set(perms)
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

def countdown(vals, target, all_orders=True, all_subsets=True):
    """
    If all_orders is False, then the numbers must be used in the order
    given.  I.e., if you give the numbers 1, 2, 3, 4, 5, 6, 7, 8, 9
    and want to make 100 and all_orders is False, then
      ((1 + (2 / 3)) / (((4 / 5) / 6) / 8)) = 100.0
    is ok, but
      (9 - (5 - (7 / ((2 - (1 / 4)) / (8 * (6 - 3)))))) = 100.0
    is not.

    if all_subsets is False, then you have to use every digit, so
      (1 - (2 * (3 * (4 * (5 + (((6 - 7) / 8) - 9)))))) = 100.0
    is ok, but
      ((1 + (2 / 3)) / (((4 / 5) / 6) / 8)) = 100.0
    is not.
    """

    vals = tuple(Value(v) for v in vals)
    closest = []
    best = None
    tries = 0
    tried = set()
    for expr in all_expressions(vals,
                                all_orders=all_orders,
                                all_subsets=all_subsets):
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
            logging.debug(
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
            yield c


# --------------------------------------------------------------------------- #

if __name__ == "__main__":
    main()

# --------------------------------------------------------------------------- #
