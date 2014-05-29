#!/usr/bin/env python
"""
http://en.wikipedia.org/wiki/Longest_common_subsequence_problem
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
    print max_common_subsequence(args)

def getopts():
    parser = optparse.OptionParser()
    parser.add_option('--verbose',  action='store_true')
    (opts, args) = parser.parse_args()
    if opts.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    return (opts, args)

# --------------------------------------------------------------------------- #

def max_common_subsequence(A, B):
    """
    >>> max_common_subsequence('', '')
    []
    >>> max_common_subsequence('1', '')
    []
    >>> max_common_subsequence('', 'a')
    []
    >>> max_common_subsequence('a', 'a')
    ['a']
    >>> max_common_subsequence('ab', 'a')
    ['a']
    >>> max_common_subsequence('ab', 'ab')
    ['a', 'b']
    >>> max_common_subsequence('ba', 'ab')
    ['b']
    >>> max_common_subsequence('bac', 'abc')
    ['b', 'c']
    >>> max_common_subsequence('bacd', 'abcd')
    ['b', 'c', 'd']
    >>> max_common_subsequence('bacd', 'abce')
    ['b', 'c']
    >>> max_common_subsequence('agasdfa', 'eitasdaaasiefaskdgsgaksd')
    ['a', 'g', 'a', 's', 'd']
    """
    len_a = len(A)
    len_b = len(B)

    max_len = [[0 for _ in xrange(len_b+1)] for _ in xrange(len_a+1)]
    prev_idx_a = [[-1 for _ in xrange(len_b+1)] for _ in xrange(len_a+1)]
    prev_idx_b = [[-1 for _ in xrange(len_b+1)] for _ in xrange(len_a+1)]

    for ii in xrange(1, len_a+1):
        for jj in xrange(1, len_b+1):
            if A[ii-1] == B[jj-1]:
                max_len[ii][jj] = max_len[ii-1][jj-1] + 1
                prev_idx_a[ii][jj] = ii-1
                prev_idx_b[ii][jj] = jj-1
            else:
                if max_len[ii][jj-1] > max_len[ii-1][jj]:
                    max_len[ii][jj] = max_len[ii][jj-1]
                    prev_idx_a[ii][jj] = ii
                    prev_idx_b[ii][jj] = jj-1
                else:
                    max_len[ii][jj] = max_len[ii-1][jj]
                    prev_idx_a[ii][jj] = ii-1
                    prev_idx_b[ii][jj] = jj

            logging.debug("a idx %s val %s b idx %s val %s max %s",
                          ii, A[ii-1], jj, B[jj-1], max_len[ii][jj])
            logging.debug("prev a %s b %s",
                          prev_idx_a[ii][jj],
                          prev_idx_b[ii][jj])
    subseq = []
    ii = len_a
    jj = len_b
    while ii > 0 and jj > 0:
        logging.debug("ii %s jj %s = %s", ii, jj, A[ii-1])
        if prev_idx_a[ii][jj] < ii and prev_idx_b[ii][jj] < jj:
            subseq.append(A[ii-1])
        (ii, jj) = (prev_idx_a[ii][jj], prev_idx_b[ii][jj])
    subseq.reverse()
    if len(subseq) != max_len[len_a][len_b]:
        raise RuntimeError("Error in algorithm, expected length {0}, got {1}".
                           format(max_len[len_a][len_b]), subseq)
    return subseq

# --------------------------------------------------------------------------- #

if __name__ == "__main__":
    main()

# --------------------------------------------------------------------------- #
