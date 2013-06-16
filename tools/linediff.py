#!/usr/bin/env python
"""
grep patt file1 file2 | linediff.py

EXAMPLES:

$ echo '1 2 3
1 2 4' | linediff.py --differ differ
- 1 2 3
?     ^
+ 1 2 4
?     ^

$ linediff.py --use_args kitten sitting far bar
r(k,s) =(i) =(t) =(t) r(e,i) =(n) +(g)
r(f,b) =(a) =(r)

$ echo '1 2 3
1 2 4' | linediff.py
=(1) =( ) =(2) =( ) r(3,4) =(
)

"""

from __future__ import absolute_import, division, with_statement

import optparse
import difflib
import logging
import sys

# ------------------------------------------------------------------

def main():
    (opts, args) = getopts()
    if opts.use_args:
        lists = args
    else:
        lists = sys.stdin.readlines()
    diff_func = get_diff_func(opts.differ)
    sys.stdout.writelines(diff_func(lists[::2], lists[1::2]))

# ------------------------------------------------------------------

def getopts():
    parser = optparse.OptionParser()
    parser.add_option('--differ',
                      choices=('differ', 'edit'),
                      help='The diff method to use')
    parser.add_option('--use_args',
                      action='store_true',
                      help='use the arguments instead of stdin')
    parser.add_option('--verbose',
                      action='store_true',
                      help='verbose mode')
    opts, args = parser.parse_args()
    if opts.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    return (opts, args)

def get_diff_func(name):
    if name == 'differ':
        return difflib_differ
    else:
        return repeat_edit_path

# ------------------------------------------------------------------

def difflib_differ(lines1, lines2):
    d = difflib.Differ()
    return list(d.compare(lines1, lines2))

# ------------------------------------------------------------------

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
        else:
            raise ValueError("unknown operation: {0}".format(self.op))

def path_str(path):
    top = ''.join((m.val1
                   if m.val1 is not None
                   else ' ')
                  for m in path)
    bottom = ''.join((m.val2
                      if m.val2 is not None
                      else ' ')
                     for m in path)
    middle = ''.join((' ' if m.op is Modification.EQUAL   else
                      'x' if m.op is Modification.REPLACE else
                      m.op)
                     for m in path)
    return '\n'.join((top, middle, bottom))
    # an alternative, simpler string:
    #return ' '.join(str(m) for m in path)

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
    # go from list1[:i+1] to list2[:j+1]
    #

    # In the first row of the matrix, list1 is empty, so all you do is
    # add all the elements of list2.  You do that for each prefix of
    # list2.
    current_cost = range(len(list2) + 1)
    current = [edit_path([], list2[:j]) for j in range(len(list2) + 1)]
    for i in range(len(list1)):
        # The first element of the next row is the column where list2
        # is empty and we start with the first i+1 elements of list1,
        # so all you do is subtract those i+1 elements.
        next_cost = [i+1]
        next_path = [edit_path(list1[:i+1], [])]
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
                                               list1[i], None)])
            logging.debug("----------------")
            logging.debug("i={0}({1}) to j={2}({3})".format(i, list1[:i+1],
                                                            j, list2[:j+1]))
            logging.debug("cost: {0}".format(next_cost[j+1]))
            logging.debug(path_str(next_path[j+1]))
            logging.debug("----------------")

        current_cost = next_cost
        current = next_path

    logging.info("cost: {0}".format(current_cost[len(list2)]))
    return path_str(current[len(list2)])

def repeat_edit_path(wordlist1, wordlist2):
    return '\n'.join(edit_path(w1.rstrip(), w2.rstrip())
                     for (w1, w2) in zip(wordlist1, wordlist2))

# ------------------------------------------------------------------

if __name__ == '__main__':
    main()
