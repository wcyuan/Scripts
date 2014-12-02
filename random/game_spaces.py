#!/usr/bin/env python
"""
This script calculates the probability of landing on given spaces in a board
game.
"""

# --------------------------------------------------------------------------- #

from __future__ import absolute_import, division, with_statement

import logging
import optparse
import numpy as np

logging.basicConfig(format='[%(asctime)s '
                    '%(funcName)s:%(lineno)s %(levelname)-5s] '
                    '%(message)s')

# --------------------------------------------------------------------------- #

EPSILON = 1e-5

# --------------------------------------------------------------------------- #

def main():
    (opts, args) = getopts()

    #print prob_space(11, equal_prob(10))
    life1 = prob_space(100, equal_prob(10))
    #print life1
    #transitions = make_transitions(equal_prob(3), 6)
    #start = transitions[:,-1]
    #start = np.zeros(6)
    #start[0] = 1
    #print start
    #print transitions
    #print np.dot(transitions, start)
    #print np.dot(transitions, np.dot(transitions, start))
    #print prob_nturns(1, equal_prob(3), 6)
    #print prob_nturns(2, equal_prob(3), 6)
    #print prob_nturns(100, dice_prob(2), 45)
    life2 = prob_landed(50, equal_prob(10), 50*10+1)
    #print life2
    print all(abs(life1[1:21] - life2[:20]) < 1e10)

    #print prob_space_mat(11, equal_prob(10))
    life3 = prob_space_mat(100, equal_prob(10))
    #print life1
    print all(abs(life1[1:11] - life3) < 1e10)

    life3 = prob_space_mat(100, equal_prob(10))
    #print life1
    print all(abs(life1[1:11] - life3) < 1e10)

    dice1 = prob_space(100, dice_prob(2))
    dice2 = prob_space_mat(100, dice_prob(2))
    print all(abs(dice1[-12:] - dice2) < 1e10)

    dice1 = prob_space(12, dice_prob(2))
    dice2 = prob_space_mat(12, dice_prob(2))
    print all(abs(dice1[-12:] - dice2) < 1e10)

    for NN in xrange(2, 11):
        print NN, prob_chart(equal_prob(NN))

    print prob_chart(dice_prob(2))

    print prob_space_vanilla(10, [Rational(1, 3)] * 3)

    o = prob_space_vanilla(100, [Polynomial([0, 1])] * 10)
    print o[-1]
    print to_frac(o[-1].eval(.1))

    NN = 4
    initial = [0] * NN
    initial[0] = 1
    o = prob_space_vanilla(10, [Polynomial([0, 1])] * NN, initial=initial)
    for x in o[NN:]:
        print x.eval(Polynomial([1, NN]))

    initial = [Rational(0)] * NN
    initial[0] = Rational(1)
    o = prob_space_vanilla(10, [Polynomial([Rational(0), Rational(1)])] * NN,
                           initial=initial)
    for x in o[NN:]:
        print x


def getopts():
    parser = optparse.OptionParser()
    parser.add_option('--verbose',       action='store_true')
    parser.add_option('--log_level')

    (opts, args) = parser.parse_args()

    if opts.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    if opts.log_level is not None:
        level = getattr(logging, opts.log_level.upper())
        logging.getLogger().setLevel(level)
        logging.info("Setting log level to %s", level)

    return (opts, args)

# --------------------------------------------------------------------------- #

# For games where each step is equal chance of N numbers
def equal_prob(n):
    return np.ones(n) / n

# For games where each step is roll of N dice
def dice_prob(n):
    return multidice_prob([6] * n)

def multidice_prob(die_sizes):
    """
    Probabilities for rolling dice of given sizes

    @param die_sizes: a sequence of die sizes.  E.g. [5, 5, 4] means
    rolling two 5-sided dice and one 4-sided die
    """
    import itertools
    # Not the most efficient way to compute this, especially
    # for 2 dice, but hopefully pretty easy to understand
    dice = [np.arange(1, sz+1) for sz in die_sizes]
    poss = sorted(sum(x) for x in (itertools.product(*dice)))
    probs = dict((k, len(tuple(g)))
        for (k, g) in itertools.groupby(poss))
    tots = sum(probs.values())
    mval = max(probs.keys())
    out = np.zeros(mval)
    for k in probs:
        out[k-1] = probs[k]
    return out / tots

# --------------------------------------------------------------------------- #

def prob_space(n, step_prob, initial=None):
    """
    Probability of landing on any of the first n squares.
    The output is a numpy array where arr[k] is the probability
    of landing on square k.  arr[0] is 1 -- conceptually, it
    represents the probability of being in the square before
    the first one.
    """
    out = np.zeros(n+1)
    out[0] = 1
    first = 1
    if initial is not None:
        ilen = initial.size
        out[0:ilen] = initial
        first = ilen
    for ii in xrange(first, n+1):
        steps = min(ii, len(step_prob))
        #print "ii: ", ii
        #print "steps: ", steps
        rev = out[::-1]
        #print "reversed: ", rev
        start = n-ii+1
        #print "past probs: ", rev[start:start+steps]
        #print "step probs: ", step_prob[:steps]
        w_probs = rev[start:start+steps] * step_prob[:steps]
        #print w_probs
        out[ii] = w_probs.sum()
    return out

# --------------------------------------------------------------------------- #

def prob_nturns(nturns, step_prob, nspaces):
    """
    probability of being on each square after n turns

    step_prob is the probability of how many steps to move in one turn
    nspaces is the size of the board (after that many spaces, the board wraps)
    """
    transitions = make_transitions(step_prob, nspaces)
    prob = transitions[:,-1]
    for _ in xrange(1, nturns):
        prob = np.dot(transitions, prob)
    return prob

def start_state(step_prob, nspaces):
    probs = step_prob.copy()
    probs.resize(nspaces)
    return probs

def make_transitions(step_prob, nspaces):
    probs = start_state(step_prob, nspaces)
    transitions = np.array([np.roll(probs, i+1) for i in xrange(len(probs))])
    transitions = transitions.transpose()
    return transitions

def prob_landed(nturns, step_prob, nspaces):
    """
    This is the probability that you landed on each square
    """
    transitions = make_transitions(step_prob, nspaces)
    prob = transitions[:,-1].copy()
    tots = prob.copy()
    for _ in xrange(1, nturns):
        prob = np.dot(transitions, prob)
        tots += prob
    return tots

# --------------------------------------------------------------------------- #

def make_transition_matrix(step_prob):
    sz = len(step_prob)
    trans = np.array([[1 if row+1 == col else 0 for col in xrange(sz)]
                      for row in xrange(sz)],
                     dtype=np.float64)
    trans[-1] = step_prob[::-1]
    return trans

def prob_space_mat(n, step_prob, initial=None):
    """
    Probability of landing on any of the first n squares.

    The probability converges to 1 / ev(step_prob).

    For equal-value probabilities, that ends up being 2 / (n + 1)

    @param n: the square whose probability you want.
    should be a positive integer.

    @param step_prob: a numpy array where arr[k] is the
    probability that each step will be of size k.

    @return: a numpy array the same size as step_prob where the
    last element is the probability of landing in square n, the
    second to last element is the probability of landing in square
    n-1, etc.
    """
    if initial is not None:
        out = initial.copy()
    else:
        out = np.zeros(len(step_prob))
        out[-1] = 1
    transitions = make_transition_matrix(step_prob)
    for _ in xrange(n):
        out = np.dot(transitions, out)
    return out

# --------------------------------------------------------------------------- #

def ev(arr):
    """
    Expected value

    >>> ev(dice_prob(1))
    3.5
    >>> ev(dice_prob(2))
    7.0
    """
    return np.dot(np.arange(1, arr.size+1), arr).sum()

# --------------------------------------------------------------------------- #

def fpeq(a, b, epsilon=EPSILON):
    return abs(a - b) < epsilon

def is_int(a, epsilon=EPSILON):
    return fpeq(a, int(round(a)), epsilon=epsilon)

def to_frac(dec, top=100, epsilon=EPSILON):
    for ii in xrange(1, top):
        if is_int(dec * ii, epsilon=epsilon):
            return "{0}/{1}".format(int(round(dec * ii)), ii)
    return dec

def prob_chart(step_prob, top_den=1000, steps=200, epsilon=EPSILON):
    out = np.zeros(step_prob.size)
    out2 = []
    for ii in xrange(step_prob.size):
        initial = np.zeros(step_prob.size)
        initial[ii] = 1
        out[ii] = prob_space_mat(steps, step_prob, initial=initial)[-1]
        out2.append(to_frac(out[ii], top=top_den, epsilon=epsilon))
    return out2

# --------------------------------------------------------------------------- #

def prob_space_vanilla(n, step_prob, initial=None):
    """
    Probability of landing on any of the first n squares.

    avoids numpy, thus can be used with complex types
    """
    out = [0] * (n+1)
    out[0] = 1
    first = 1
    if initial is not None:
        ilen = len(initial)
        out[0:ilen] = initial
        first = ilen
    for ii in xrange(first, n+1):
        steps = min(ii, len(step_prob))
        #print "ii: ", ii
        #print "steps: ", steps
        rev = out[::-1]
        #print "reversed: ", rev
        start = n-ii+1
        #print "past probs: ", rev[start:start+steps]
        #print "step probs: ", step_prob[:steps]
        for jj in xrange(steps):
            out[ii] = step_prob[jj] * rev[start+jj] + out[ii]
    return out

# --------------------------------------------------------------------------- #

class Polynomial(object):
    """
    Represents a polynomial in one variable.
    """
    def __init__(self, powers=None):
        """
        @param powers: an iterable of coefficients such that the
        nth value in the iterable (zero-indexed) is the coefficient
        for x^n
        """
        if powers is None:
            powers = ()
        self._powers = tuple(powers)
    @property
    def powers(self):
        return self._powers
    def __repr__(self):
        return "{cn}(powers={self.powers!r})".format(
            cn=self.__class__.__name__, self=self)
    def __str__(self):
        if len(self.powers) == 0:
            return "0"
        highest = len(self.powers) - 1
        def make_term(power, coeff, highest):
            if power == highest:
                op = ""
            elif coeff < 0:
                op = "- "
                coeff = -coeff
            else:
                op = "+ "

            if power != 0:
                if coeff == 1:
                    coeff = ""
                elif coeff == -1:
                    coeff = "-"

            if power == 0:
                power = ""
            elif power == 1:
                power = "x"
            else:
                power = "x^{0}".format(power)

            return "{0}{1}{2}".format(op, coeff, power)
        return " ".join(make_term(power, coeff, highest)
                        for (power, coeff) in
                        reversed(tuple(enumerate(self.powers)))
                        if coeff != 0)
    def __add__(self, other):
        if isinstance(other, Polynomial):
            import itertools
            return Polynomial([x if y is None else y if x is None else x+y
                               for (x, y) in
                               itertools.izip_longest(
                                   self.powers, other.powers, fillvalue=None)])
        else:
            return Polynomial(coeff+other if power == 0 else coeff
                              for (power, coeff) in enumerate(self.powers))
    def __radd__(self, other):
        return self + other
    def __iadd__(self, other):
        self._powers = (self + other).powers
        return self
    def __mul__(self, other):
        if isinstance(other, Polynomial):
            powers = [0] * (len(self.powers) + len(other.powers))
            for ii in xrange(len(self.powers)):
                for jj in xrange(len(other.powers)):
                    powers[ii+jj] = (self.powers[ii]*other.powers[jj] +
                                     powers[ii+jj])
            while powers and powers[-1] == 0:
                powers.pop()
            return Polynomial(powers)
        else:
            return Polynomial(i * other for i in self.powers)
    def __sub__(self, other):
        return self + (other * -1)
    def __rmul__(self, other):
        return self + other
    def __cmp__(self, other):
        import itertools
        coeffs = tuple(itertools.izip_longest(
            self.powers, other.powers, fillvalue=None))
        for (scoeff, ocoeff) in reversed(coeffs):
            val = cmp(scoeff, ocoeff)
            if val != 0:
                return val
        return 0
    def __hash__(self):
        return hash(self.powers)
    def eval(self, n):
        val = 0
        var = 1
        for coeff in self.powers:
            val = coeff * var + val
            var = n * var
        return val

# --------------------------------------------------------------------------- #

class Rational(object):
    """
    >>> print Rational(1, 3)
    1/3
    >>> print Rational(1, 3) * Rational(1, 4)
    1/12
    """
    def __init__(self, num, den=1):
        self._num, self._den = self._reduce(num, den)
    @property
    def num(self):
        return self._num
    @property
    def den(self):
        return self._den
    def __repr__(self):
        return "{cn}(num={self._num!r}, den={self._den!r})".format(
            cn=self.__class__.__name__, self=self)
    def __str__(self):
        if self.den == 1:
            return str(self.num)
        return "{0}/{1}".format(self.num, self.den)
    @classmethod
    def _gcd(cls, a, b):
        while b != 0:
            t = b
            b = a % b
            a = t
        return a
    @classmethod
    def _lcm(cls, a, b):
        return a*b // cls._gcd(a, b)
    @classmethod
    def _reduce(cls, a, b):
        gcd = cls._gcd(a, b)
        return a // gcd, b // gcd
    def __hash__(self):
        return hash(self.num, self.den)
    def __cmp__(self, other):
        if not isinstance(other, Rational):
            return cmp(self, Rational(num=other))
        gcd = self._gcd(self.den, other.den)
        return cmp(self.num * other.den * gcd, other.num * self.den * gcd)
    def __add__(self, other):
        if isinstance(other, Rational):
            gcd = self._gcd(self.den, other.den)
            return Rational(
                num=self.num * other.den * gcd + other.num * self.den * gcd,
                den=self.den * other.den * gcd)
        else:
            return Rational(num=self.num + other * self.den, den=self.den)
    def __radd__(self, other):
        return self + other
    def __iadd__(self, other):
        new = self + other
        self._num = new.num
        self._den = new.den
        return self
    def __sub__(self, other):
        return self + (other * -1)
    def __mul__(self, other):
        if isinstance(other, Rational):
            return Rational(num=self.num*other.num, den=self.den*other.den)
        else:
            return Rational(num=self.num*other, den=self.den)
    def __rmul__(self, other):
        return self * other
    def __div__(self, other):
        if isinstance(other, Rational):
            return Rational(num=self.num*other.den, den=self.den*other.num)
        else:
            return Rational(num=self.num, den=self.den*other)

# --------------------------------------------------------------------------- #

if __name__ == "__main__":
    main()

# --------------------------------------------------------------------------- #
