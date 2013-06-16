#!/usr/bin/env python
"""
grep patt file1 file2 | linediff.py

"""

from __future__ import absolute_import, division, with_statement

from difflib import Differ
import sys

# ------------------------------------------------------------------

def main():
    #diff_func = get_diff_func(sys.argv[0] if len(sys.argv) > 0 else None)
    #lines = sys.stdin.readlines()
    #sys.stdout.writelines(diff_func(lines[::2], lines[1::2]))
    print ' '.join(str(m) for m in edit_path(sys.argv[1], sys.argv[2]))

# ------------------------------------------------------------------

def get_diff_func(arg):
    if arg == 'differ':
        return difflib_differ
    else:
        return difflib_differ

def difflib_differ(lines1, lines2):
    d = Differ()
    return list(d.compare(lines1, lines2))

class Modification(object):
    EQUAL='='
    ADD='+'
    SUB='-'
    REPLACE='r'
    def __init__(self, op, val1, val2):
        self.op = op
        self.val1 = val1
        self.val2 = val2

    @property
    def value(self):
        return 0 if self.op == self.EQUAL else 1

    def __str__(self):
        if self.op == self.EQUAL:
            return '{0}({1})'.format(self.op, self.val1)
        if self.op == self.ADD:
            return '{0}({1})'.format(self.op, self.val2)
        if self.op == self.SUB:
            return '{0}({1})'.format(self.op, self.val1)
        if self.op == self.REPLACE:
            return '{0}({1},{2})'.format(self.op, self.val1, self.val2)

def edit_path(list1, list2):
    """
    Modified from:
    http://en.wikipedia.org/wiki/Levenshtein_distance#Iterative_with_two_matrix_rows
    """
    if len(list1) == 0 and len(list2) == 0:
        return []
    if len(list1) == 0:
        return [Modification(Modification.ADD, None, e) for e in list2]
    if len(list2) == 0:
        return [Modification(Modification.SUB, e, None) for e in list1]

    # current and next are rows in the matrix:
    #    - e1 e2 e3 e4 e5
    # -
    # f1
    # f2
    # f3
    # f4
    #
    # where list1 = [f1, f2, f3, f4]
    # and   list2 = [e1, e2, e3, e4, e5]
    # and the element of the matrix for [ei, fj] is the edit path to
    # go from list1[:i] to list2[:j]
    #

    # In the first row of the matrix, list1 is empty, so all you do is
    # add all the elements of list2.  You do that for each prefix of
    # list2.
    current_cost = range(len(list2) + 1)
    current = [edit_path([], list2[:j]) for j in range(len(list2) + 1)]
    for i in range(len(list1)):
        # The first element of the next row is the column where list2
        # is empty, so all you do is subtract all the elements of
        # list1.
        next_cost = [i]
        next_path = [edit_path(list1[:i], [])]
        for j in range(len(list2)):
            # In the inductive step, imagine that you know the edit
            # paths for these cases:
            #   (from ABCD  to EFG)
            #   (from ABCD  to EFGY)
            #   (from ABCDX to EFG)
            # and you want to know the edit path for
            #   (from ABCDX to EFGY)
            # the possibilities are
            #   (from ABCD  to EFG)  + (X==Y)
            #   (from ABCD  to EFG)  + (replace X with Y)
            #   (from ABCD  to EFGY) + (subtract X)
            #   (from ABCDX to EFG)  + (add Y)
            cost_add = next_cost[j] + 1
            cost_sub = current_cost[j+1] + 1
            cost_repl = current_cost[j] + (0 if list1[i] == list2[j] else 1)
            next_cost.append(min(cost_add, cost_sub, cost_repl))
            if next_cost[j+1] == cost_repl:
                next_path.append(current[j] +
                                 [Modification((Modification.EQUAL
                                                if list1[i] == list2[j]
                                                else Modification.REPLACE),
                                               list1[i], list2[j])])
            elif next_cost[j+1] == cost_add:
                next_path.append(next_path[j] +
                                 [Modification(Modification.ADD,
                                               None, list2[j])])
            elif next_cost[j+1] == cost_sub:
                next_path.append(current[j+1] +
                                 [Modification(Modification.SUB,
                                               None, list1[i])])

        current_cost = next_cost
        current = next_path

    return current[len(list2)]

# ------------------------------------------------------------------

if __name__ == '__main__':
    main()
