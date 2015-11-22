#!/usr/bin/env python
"""
# https://en.wikipedia.org/wiki/Derangement
# http://math.stackexchange.com/questions/14666/number-of-permutations-of-n-where-no-number-i-is-in-position-i
# http://www.math.harvard.edu/~lurie/155.html
# http://www.math.harvard.edu/~lurie/155notes/lecture3.pdf
# http://www.math.harvard.edu/~lurie/155notes/lecture4.pdf
"""


# --------------------------------------------------------------------

from __future__ import absolute_import, division, with_statement

import itertools

# --------------------------------------------------------------------

def main():
    # 44
    print len(tuple(different_lists(5)))

    # 265
    print len(tuple(different_lists(6)))

    # 1854
    print len(tuple(different_lists(7)))

    # 14833
    print len(tuple(different_lists(8)))

    import timeit
    print timeit.timeit(lambda: len(tuple(different_lists(8))), number=10)
    print timeit.timeit(lambda: len(tuple(all_diff_perms(8))), number=10)

# --------------------------------------------------------------------

def different_lists(N):
    """List all permutations of a list where no element is in its original place.
    """
    if False:
        if N < 2:
            return
        if N == 2:
            # 10 is the only possibility
            yield (1, 0)
            return
        if N == 3:
            # these are the only possibilities:
            # 120
            # 201
            # these are all invalid:
            # 012
            # 021
            # 102
            # 210
            yield (1, 2, 0)
            yield (2, 0, 1)
            return
        if N == 4:
            # 9 possibilities:
            yield (1, 0, 3, 2)
            yield (1, 2, 3, 0)
            yield (1, 3, 0, 2)
            yield (2, 0, 3, 1)
            yield (2, 3, 0, 1)
            yield (2, 3, 1, 0)
            yield (3, 0, 1, 2)
            yield (3, 2, 0, 1)
            yield (3, 2 ,1, 0)
            return
    # might not be terribly efficient.  For example, even though we know that we don't have to
    # consider permutations starting with 0, this will consider and reject all such permutations
    for perm in itertools.permutations(range(N)):
        for (ii, nn) in enumerate(perm):
            if ii == nn:
                break
        else:
            yield perm

# this solves the same problem
# This seems like it might be more efficient, since it doesn't
# consider permutations we don't care about, but it's actually
# less efficient, possibly because it uses recursion and 
# maybe because itertools is probably highly optimized.
def all_diff_perms(N, I=0, remain=None):
    if remain is None:
        remain = range(N)
    if not remain:
        yield ()
        return
    for ii, elt in enumerate(remain):
        if elt == I:
            continue
        for perm in all_diff_perms(N, I+1, remain = remain[:ii] + remain[ii+1:]):
            yield (elt,) + perm

# --------------------------------------------------------------------

def fill_schedule(N, R, schedule=None, by_team=None, home_away=None):
    if not schedule:
        schedule = make_empty_schedule()
        by_team = get_by_team(schedule)
        home_away = get_home_away(schedule)
    for rnd in make_rounds(schedule, by_team, home_away):
        schedule = add_round(schedule, rnd)

        schedule = remove_last_round(schedule)

def make_rounds(schedule=None, by_team=None, home_away=None):
    # go through all permutations of teams, throw out any that
    # conflict with the existing schedule.
    pass

# --------------------------------------------------------------------

if __name__ == "__main__":
    main()

# --------------------------------------------------------------------
