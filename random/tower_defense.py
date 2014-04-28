#!/usr/bin/env python
"""
http://www.ch24.org/static/archive/2013/2013_finals.pdf

A. Tower Defense
Zombies are after you. You need to improvise some
sort of barricade from whatever you find in the streets.
The most useful items are large cardboard boxes you
load with bricks, as you can build tall stacks of them.
Given N boxes with positive weight, strength and
height build the tallest tower (each item in the tower
must have enough strength to bear the sum of the
weights of the items above).

http://www.instructables.com/id/Free-Boxes-Free-Waste-Removal/
Input
The first line of the input contains N, the following N lines each contains three integers H,W,S, the height,
weight and strength of an item.
Output
The output should give the tallest tower: the first line is the height and the second line the list of items of
the tower from the bottom to top (items are indexed from 0 based on their position in the input).
Example input
10
4 3 8
5 2 9
7 1 4
3 2 5
4 1 3
9 4 6
1 1 5
1 3 7
2 2 4
3 2 6
Example output
29
1 5 3 6 2 4
"""

# --------------------------------------------------------------------------- #

from __future__ import absolute_import, division, with_statement

import logging
import optparse
import sys

logging.basicConfig(format='[%(asctime)s '
                    '%(funcName)s:%(lineno)s %(levelname)-5s] '
                    '%(message)s')

# --------------------------------------------------------------------------- #

def main():
    (opts, args) = getopts()

    if opts.test:
        import doctest
        doctest.testmod(verbose=opts.verbose)
        return

    if args:
        boxes = Tower.from_tuples(grouper((int(a) for a in args), 3))
    elif opts.example:
        boxes = Tower.from_tuples(((4, 3, 8), (5, 2, 9), (7, 1, 4), (3, 2, 5),
                                   (4, 1, 3), (9, 4, 6), (1, 1, 5), (1, 3, 7),
                                   (2, 2, 4), (3, 2, 6)))
    else:
        boxes = read_input()
    tower = best_tower_prune(boxes)
    print sum(boxes[b].height for b in tower.path)
    print ' '.join(str(p) for p in tower.path)

def getopts():
    parser = optparse.OptionParser()
    parser.add_option('--verbose',  action='store_true')
    parser.add_option('--info',  action='store_true')
    parser.add_option('--example',  action='store_true')
    parser.add_option('--test',  action='store_true')
    (opts, args) = parser.parse_args()
    if opts.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    elif opts.info:
        logging.getLogger().setLevel(logging.INFO)
    return (opts, args)

# --------------------------------------------------------------------------- #

class Tower(object):
    """
    A tower object represents a box, or a sequence of boxes, one
    inside another.

    The path member is a list of box ids which tells you what the
    tower is made up of.

    """
    def __init__(self, path, height, weight, strength):
        self.path = tuple(path)
        self.height = height
        self.weight = weight
        self.strength = strength

    def __repr__(self):
        return ('{cn}({self.path!r}, {self.height!r}, '
                '{self.weight!r}, {self.strength!r})'.
                format(cn=self.__class__.__name__, self=self))

    def vals(self):
        return (self.path, self.height, self.weight, self.strength)

    def __hash__(self):
        return hash(self.vals())

    def __cmp__(self, other):
        return cmp(self.vals(), other.vals())

    def remaining_strength(self, other):
        return min(self.strength - other.weight, other.strength)

    def overlaps(self, other):
        return len(set(self.path) & set(other.path)) > 0

    def can_hold(self, other):
        return (not self.overlaps(other) and
                self.remaining_strength(other) >= 0)

    def stack(self, other):
        return self.__class__(self.path + other.path,
                              self.height + other.height,
                              self.weight + other.weight,
                              self.remaining_strength(other))

    def is_always_better_than(self, other):
        """
        If this box is at least as tall, at least as light, at least as
        strong, and uses the same or fewer boxes as another tower, we can
        ignore the other tower, we would always prefer this one.
        """
        return (self.height >= other.height and
                self.weight <= other.weight and
                self.strength >= other.strength and
                len(set(other.path) - set(self.path)) == 0)

    @classmethod
    def from_tuples(cls, seq):
        """
        A convenience method which takes in a sequence of tuples of
        (height, weight, strength).  It creates a box for each tuple,
        give the box an id, and returns a one-box tower for each box
        """
        return [cls((id,), *tup) for (id, tup) in enumerate(seq)]

    @classmethod
    def from_boxlist(cls, boxes, seq):
        return reduce(lambda a, b: a.stack(boxes[b]), seq[1:], boxes[seq[0]])

# --------------------------------------------------------------------------- #

def input_to_tuples():
    """
    Create towers for each box given
    """
    number = 0
    for line in sys.stdin:
        if number == 0:
            number = int(line)
            continue
        (height, weight, strength) = line.split()
        yield (int(height), int(weight), int(strength))

def read_input():
    return Tower.from_tuples(input_to_tuples())

# From the recipes section of the itertools documentation
def grouper(iterable, n, fillvalue=None):
    import itertools
    "Collect data into fixed-length chunks or blocks"
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx
    args = [iter(iterable)] * n
    return itertools.izip_longest(fillvalue=fillvalue, *args)

# --------------------------------------------------------------------------- #

def best_tower_tuples(*tuples):
    """
    >>> best_tower_tuples()
    ()
    >>> best_tower_tuples((1, 1, 1))
    (0,)
    >>> best_tower_tuples((2, 3, 4))
    (0,)
    >>> best_tower_tuples((2, 3, 4), (1, 1, 1))
    (0, 1)
    >>> best_tower_tuples((1, 1, 1), (2, 3, 4))
    (1, 0)
    >>> boxes = Tower.from_tuples(((4, 3, 8), (5, 2, 9), (7, 1, 4), (3, 2, 5), (4, 1, 3), (9, 4, 6), (1, 1, 5), (1, 3, 7), (2, 2, 4), (3, 2, 6)))
    >>> best_tower(boxes).path
    (0, 5, 4, 2, 1)
    >>> best_tower_prune(boxes).path
    (1, 5, 2, 4, 0)


    My algorithms find (0, 5, 4, 2, 1) and (1, 5, 2, 4, 0) instead of
    the suggested (1, 5, 3, 6, 2, 4), but all seem to be valid towers
    of height 29.

    """
    return best_tower_prune(Tower.from_tuples(tuples)).path

def best_tower(boxes, base=None):
    """
    I think this works, but it's not very efficient.  In the worst
    case (e.g., all weights much less than all strengths, which should
    actually be a very simple case), it will be n factorial.

    """
    if base is None:
        base = Tower((), 0, 0, sum(b.strength for b in boxes) + 1)
    best = base
    for box in boxes:
        if base.strength >= box.weight:
            stacked = best_tower(set(boxes) - set([box]), base=base.stack(box))
            if stacked.height > best.height:
                best = stacked
    return best

def best_tower_prune(boxes):
    """
    best_tower can be considered a recurive depth-first-search.

    best_tower_iter, on the other hand, is like a
    breadth-first-search.  We start with the current set of towers as
    the towers with just one box.  Then for each tower in the current
    set (towers with n boxes), we try to add another box to form the
    next set of towers to look at (towers with n+1 boxes).

    After we create the next_set, we prune it by removing towers which
    are no better than other towers on the list.

    This is a practical solution to the problem where the weights are
    small compared to the strengths, but I'm not sure that it is
    enough to bound the worst-case asymptotic running time to
    something less than n!.

    """
    if not boxes:
        return Tower((), 0, 0, 0)
    next_towers = boxes
    best = []
    while next_towers:
        towers = next_towers
        next_towers = []
        all_next_towers = []
        for tower in towers:
            if not best or tower.height > best[0].height:
                best = [tower]
            elif best[0].height == tower.height:
                best.append(tower)
            for box in boxes:
                if tower.can_hold(box):
                    all_next_towers.append(tower.stack(box))
        supersets = dict()
        for tower1 in all_next_towers:
            for tower2 in all_next_towers:
                if tower2 == tower1:
                    continue
                if tower2 in supersets:
                    continue
                if tower2.is_always_better_than(tower1):
                    supersets[tower1] = tower2
                    logging.debug("skipping %s because %s is a superset",
                                  tower1, tower2)
                    break
            else:
                next_towers.append(tower1)
        logging.debug("next towers: %s", next_towers)
    # This doesn't really find all best towers, it only finds the ones
    # that use different boxes.  For example, if (0, 5, 4, 2, 1) and
    # (1, 5, 2, 4, 0) are both valid and have the same height, one
    # will be cut out as "always better than" the other, so we won't
    # try to remember it.
    logging.info("All best towers: %s", best)
    return best[0]

# --------------------------------------------------------------------------- #

if __name__ == "__main__":
    main()

# --------------------------------------------------------------------------- #
