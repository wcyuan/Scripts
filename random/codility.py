#!/usr/bin/env python
"""
My answers to a test Codility Assessment
"""

# --------------------------------------------------------------------------- #

from __future__ import absolute_import, division, with_statement

import logging
import optparse

logging.basicConfig(format='[%(asctime)s '
                    '%(funcName)s:%(lineno)s %(levelname)-5s] '
                    '%(message)s')

# --------------------------------------------------------------------------- #

def main():
    (opts, args) = getopts()
    test1()
    test2()
    testdemo()

def getopts():
    parser = optparse.OptionParser()
    parser.add_option('--verbose',  action='store_true')
    (opts, args) = parser.parse_args()
    if opts.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    return (opts, args)

# --------------------------------------------------------------------------- #

# Demo

# http://blog.codility.com/2011/03/solutions-for-task-equi.html
#
# The equilibrium index of a sequence is an index such that the sum of elements
# at lower indexes is equal to the sum of elements at higher indexes. For example,
# in a sequence A:
# A[0]=-7 A[1]=1 A[2]=5 A[3]=2 A[4]=-4 A[5]=3 A[6]=0
# 3 is an equilibrium index, because:
# A[0]+A[1]+A[2]=A[4]+A[5]+A[6]
# 6 is also an equilibrium index, because:
# A[0]+A[1]+A[2]+A[3]+A[4]+A[5]=0
# (The sum of zero elements is zero) 7 is not an equilibrium index - because
# it is not a valid index of sequence A. If you still have doubts, here is a
# precise definition: The integer k is an equilibrium index of a sequence
# A[0],A[1]..,A[n-1] if and only if 0<= k and sum(A[0..(k-1)])=sum(A[(k+1)..(n-1)]).
# Assume the sum of zero elements is equal to zero. 
#
# Write a function
# int equi(int A[], int n)
# that, given a sequence, returns its equilibrium index (any) or -1 if no
# equilibrium index exists. Assume that the sequence may be very long.

def dsolution(A):
    # XXX this doesn't work...

    # write your code in Python 2.7
    # from_start[i] = sum(A[0]..A[i])
    from_start = partials(A)
    # from_end[i] = sum(A[i]..A[N-1])
    from_end = partials(A[::-1])
    from_end.reverse()
    if len(from_end) > 1 and from_end[1] == 0:
        return 0
    for ii in xrange(1, len(A)-1):
        if from_start[ii-1] == from_end[ii+1]:
            return ii
    if len(from_start) > 1 and from_start[-1] == 0:
        return len(A) - 1
    return -1

def dsolution2(A):
    from_start = 0
    from_end = sum(A)
    for ii in xrange(len(A)):
        from_end -= A[ii]
        if from_end == from_start:
            return ii
        from_start += A[ii]
    return -1

def partials(lst, start=0):
    retval = []
    for ii in xrange(len(lst)):
        start += lst[ii]
        retval.append(start)
    return retval

def testdemo():
    for fcn in dsolution, dsolution2:
        print "HERE"
        print fcn([]) == -1
        print fcn([0]) == 0
        print fcn([1]) == 0
        print fcn([1, 0]) == 0
        print fcn([-1, -1, 2, 500]) == 3

# --------------------------------------------------------------------------- #
# Task 1:
# Given a string with alphanumerics and dashes ('-')
# Convert everything to uppercase.
# The dashes are in the wrong place
# There should be a dash every K characters
# If any group must have fewer than K characters, it should be the first group

SEP = "-"

def t1solution(S, K):
    # write your code in Python 2.7
    S = "".join(S.split("-")).upper()
    L = len(S)
    F = L % K
    if F == 0:
        F = K
    return "".join(helper1(S, K, F))

def helper1(S, K, N, sep=SEP):
    for ii in xrange(len(S)):
        if N == 0:
            yield sep
            N = K
        yield S[ii]
        N -= 1

def t1solution2(S, K, sep=SEP):
    # write your code in Python 2.7
    S = "".join(S.split(sep)).upper()
    return sep.join(groups_of_k(S, K))

def groups_of_k(input_string, group_size):
    length = len(input_string)
    remainder = length % group_size
    if remainder != 0:
        yield input_string[:remainder]
        input_string = input_string[remainder:]
    remainder = group_size
    ret = ""
    for ch in input_string:
        if remainder == 0:
            yield ret
            remainder = group_size
            ret = ""
        ret += ch
        remainder -= 1
    if ret:
        yield ret

def test1():
    for fcn in t1solution, t1solution2:
        print fcn('2-4A0r7-4k', 4) == "24A0-R74K"
        print fcn('2-4A0r7-4k', 3) == "24-A0R-74K"
        print fcn('r', 1) == "R"

# --------------------------------------------------------------------------- #
# Task 2:
# Given a binary search tree, return the size of the largest subtree whose
# nodes are in the range [A, B]
#

class Tree(object):
    def __init__(self, x, l, r):
        self.x = x
        self.l = l if l is None else Tree(*l)
        self.r = r if r is None else Tree(*r)
    def __repr__(self):
        return "Tree({t.x}, {t.l}, {t.r})".format(t=self)

def t2solution(A, B, T):
    # write your code in Python 2.7
    return helper(A, B, T)[1]

def helper(A, B, T):
    if T is None:
        return (True, 0)
    (left_is_in_range, left_size) = helper(A, B, T.l)
    (right_is_in_range, right_size) = helper(A, B, T.r)
    if left_is_in_range and right_is_in_range and A <= T.x and B >= T.x:
        in_range = True
        my_size = left_size + right_size + 1
    else:
        in_range = False
        my_size = max(left_size, right_size)
    return (in_range, my_size)

def test2():
    tree = Tree(28, (19, (8, None, None), 
                         (22, None, (23, None, None))), 
                    (33, (29, None, None),
                         (37, None, (40, None, None))))
    print tree
    print 4 == t2solution(15, 40, tree)

# --------------------------------------------------------------------------- #

if __name__ == "__main__":
    main()

# --------------------------------------------------------------------------- #
