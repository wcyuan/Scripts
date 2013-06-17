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
    """
    Pretty print a list of Modifications.  This assumes that each
    value is a string and that all the strings have length 1.
    """
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

    This returns the smallest set of Modifications necessary to change
    list1 to list2 using the operations Add, Subtract, or Replace (as
    well as the nop operation Equal).  The number of non-Equal
    operations is usually referred to as the "edit distance", so I
    think of this as returning the "edit path", though it would be
    more accurately called something like the "minimum-edit-distance
    operations".

    This function is generally passed in strings as input, not lists,
    but the function would work on lists too.  We refer to them lists
    in order to be more general.
    """

    # Handle base cases.
    # If we are given two empty lists, return the empty list of
    # Modifications.
    if len(list1) == 0 and len(list2) == 0:
        return []
    # If the first list is empty, then the shortest path is to just
    # add each element of the second list.
    if len(list1) == 0:
        return [Modification(Modification.ADD, None, e) for e in list2]
    # If the second list is empty, then the shortest path is to just
    # remove each element of the fist list.
    if len(list2) == 0:
        return [Modification(Modification.SUB, e, None) for e in list1]

    # Otherwise, we need to construct this matrix:
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
    # We don't need to remember the full matrix.  We only need to
    # remember the previous row and the row that we are currently
    # filling in.  The previous row is called "current" and the row we
    # are currently filling in is called "next".

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
    return current[len(list2)]

def edit_path_len(list1, list2):
    """
    edit_path is not so fast and will have trouble with long
    lists/strings.  So if the lists are longer than that, break them
    into chunks of 100.

    This obviously doesn't work perfectly.  If the only difference
    between two lists is that you add an element to the second list,
    then instead of just seeing the addition in the first chunk, for
    each chunk of 100 elements, you'll see an addition at the
    beginning and a removal at the end.  But at least it allows the
    function to run in a reasonable amount of time.
    """
    len_at_a_time = 100
    maxlen = max(len(list1), len(list2))
    lengths = range(0, maxlen, len_at_a_time) + [maxlen]
    sep = "\n{0}\n".format('=' * len_at_a_time)
    return sep.join(path_str(edit_path(list1[start:end], list2[start:end]))
                    for (start, end) in zip(lengths[:-1], lengths[1:]))

def repeat_edit_path(wordlist1, wordlist2):
    """
    Given two lists of strings, run edit_path_len on each
    corresponding pair of strings.  Also, remove trailing whitespace
    on the strings before passing them to edit_path_len.  This is
    useful because otherwise they will usually have a newline
    character at the end (if we read the strings from stdin instead of
    as arguments)
    """
    return '\n'.join(edit_path_len(w1.rstrip(), w2.rstrip())
                     for (w1, w2) in zip(wordlist1, wordlist2)) + "\n"

# ------------------------------------------------------------------

if __name__ == '__main__':
    main()
