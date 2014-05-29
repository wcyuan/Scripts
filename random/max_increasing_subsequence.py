#!/usr/bin/env python
"""
http://en.wikipedia.org/wiki/Longest_increasing_subsequence
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
    print max_increasing_subsequence(args)

def getopts():
    parser = optparse.OptionParser()
    parser.add_option('--verbose',  action='store_true')
    (opts, args) = parser.parse_args()
    if opts.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    return (opts, args)

# --------------------------------------------------------------------------- #

def max_increasing_subsequence(lst):
    """
    This is an O(N*log(N)) algorithm where N is the size of the input list

    In the worst case, consider:
      [1, 2, 1, 3, 1, 4, 1, 5, 1, 6, 1, 7, ...]

    In this list, the max increasing subsequence has a length of n/2,
    and each time you hit a 1, you have to go back through the
    existing lengths, to confirm that there is no subsequence of that
    length whose max value is less than 1


    >>> max_increasing_subsequence([])
    []
    >>> max_increasing_subsequence([23])
    [23]
    >>> max_increasing_subsequence([1, 2, 3])
    [1, 2, 3]
    >>> max_increasing_subsequence([1, 3, 2])
    [1, 2]
    >>> max_increasing_subsequence([1, 5, 2, 5])
    [1, 2, 5]
    >>> max_increasing_subsequence([1, 5, 2, 5, 100, 24, 254, 1, 2, -1, 5])
    [1, 2, 5, 24, 254]
    >>> max_increasing_subsequence([1, 5, 2, 5, 100, 24, 254, 1, 2, 3, 5, 8, 10])
    [1, 2, 3, 5, 8, 10]
    >>> max_increasing_subsequence([1, 5, 2, 5, 100, 24, 254, 1, 2, 3, 5, 8, 10])
    [1, 2, 3, 5, 8, 10]
    >>> max_increasing_subsequence([10, 1, 9, 2])
    [1, 2]
    >>> max_increasing_subsequence([10, 1, 9, 5, 4, 3, 2, 1, 0, 4])
    [1, 2, 4]
    >>> max_increasing_subsequence([10, 1, 9, 0, 4])
    [0, 4]

    """
    # The length of the maximum increasing subsequence seen so far
    max_len = 0
    # For each length, the index of the minimum max-value of all
    # subsequences of that length.  Note that because the list is
    # zero-indexed, the index for length L is stored in the array at
    # spot L-1
    min_val_idx = []
    # Map from each index I to the index J of the previous element in
    # the max increasing subsequence that ends at I.  At the end,
    # we'll use this map to walk backwards and find the max
    # subsequence.
    prev = []

    for ii in xrange(len(lst)):
        # Find the length of the maximum increasing subsequence that
        # ends at ii.
        if False:
            # this is a linear search
            length = max_len
            while length > 0:
                if lst[ii] > lst[min_val_idx[length-1]]:
                    # this value can add to the increasing subsequence of
                    # this length!
                    break
                length -= 1
            length += 1
        else:
            # We can do it as a binary search, so it's O(log(max_len))
            # time instead of O(max_len) time.
            length = 1
            hi = max_len
            while length <= hi:
                mid = int((length + hi) / 2)
                if lst[min_val_idx[mid-1]] < lst[ii]:
                    length = mid+1
                else:
                    hi = mid-1

        # Now update our state variables
        if max_len < length:
            max_len = length
            min_val_idx.append(ii)
        else:
            # Somewhat surprisingly, you don't need this check, it
            # will always be true
            # if lst[ii] < lst[min_val_idx[length-1]]:
            min_val_idx[length-1] = ii

        logging.debug("Index %s value %s len %s min_val_idx %s max_len %s",
                      ii, lst[ii], length, min_val_idx[length-1], max_len)

        prev.append(min_val_idx[length-2] if length > 1 else -1)

    subseq = []
    if max_len > 0:
        idx = min_val_idx[max_len-1]
        while idx >= 0:
            subseq.append(lst[idx])
            idx = prev[idx]
    logging.debug("min_val_idx %s", min_val_idx)
    logging.debug("prev %s", prev)
    return list(reversed(subseq))

# --------------------------------------------------------------------------- #

if __name__ == "__main__":
    main()

# --------------------------------------------------------------------------- #
