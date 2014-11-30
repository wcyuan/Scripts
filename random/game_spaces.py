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

def main():
    (opts, args) = getopts()

    #prob_to_three = equal_prob(3)
    prob_to_ten = equal_prob(10)
    #prob_two_dice = dice_prob(2)
    #print prob_space(11, prob_to_ten)
    life1 = prob_space(100, prob_to_ten)
    #print life1
    #transitions = make_transitions(prob_to_three, 6)
    #start = transitions[:,-1]
    #start = np.zeros(6)
    #start[0] = 1
    #print start
    #print transitions
    #print np.dot(transitions, start)
    #print np.dot(transitions, np.dot(transitions, start))
    #print prob_nturns(1, prob_to_three, 6)
    #print prob_nturns(2, prob_to_three, 6)
    #print prob_nturns(100, prob_two_dice, 45)
    life2 = prob_landed(50, prob_to_ten, 50*10+1)
    #print life2
    print all(abs(life1[1:21] - life2[:20]) < 1e10)

    #print prob_space_mat(11, prob_to_ten)
    life3 = prob_space_mat(100, prob_to_ten)
    #print life1
    print all(abs(life1[1:11] - life3) < 1e10)

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
    import itertools
    # Not the most efficient way to compute this, especially
    # for 2 dice, but hopefully pretty easy to understand
    die = np.arange(1, 7)
    poss = sorted(sum(x) for x in (itertools.product(die, repeat=n)))
    probs = dict((k, len(tuple(g)))
        for (k, g) in itertools.groupby(poss))
    tots = sum(probs.values())
    mval = max(probs.keys())
    out = np.zeros(mval)
    for k in probs:
        out[k-1] = probs[k]
    return out / tots

def prob_space(n, step_prob):
    """
    Probability of landing on any of the first n squares.
    The output is a numpy array where arr[k] is the probability
    of landing on square k.  arr[0] is 1 -- conceptually, it
    represents the probability of being in the square before
    the first one.
    """
    out = np.zeros(n+1)
    out[0] = 1
    for ii in xrange(1, n+1):
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

def make_transition_matrix(step_prob):
    sz = len(step_prob)
    trans = np.array([[1 if row+1 == col else 0 for col in xrange(sz)]
                      for row in xrange(sz)],
                     dtype=np.float64)
    trans[-1] = step_prob
    return trans

def prob_space_mat(n, step_prob):
    """
    Probability of landing on any of the first n squares.

    @param n: the square whose probability you want.
    should be a positive integer.

    @param step_prob: a numpy array where arr[k] is the
    probability that each step will be of size k.

    @return: a numpy array the same size as step_prob where the
    last element is the probability of landing in square n, the
    second to last element is the probability of landing in square
    n-1, etc.
    """
    out = np.zeros(len(step_prob))
    out[-1] = 1
    transitions = make_transition_matrix(step_prob)
    for _ in xrange(n):
        out = np.dot(transitions, out)
    return out

# --------------------------------------------------------------------------- #

if __name__ == "__main__":
    main()

# --------------------------------------------------------------------------- #
