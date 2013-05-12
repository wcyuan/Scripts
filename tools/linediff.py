#!/usr/bin/env python
"""
grep patt file1 file2 | linediff.py

"""

from __future__ import absolute_import, division, with_statement

from difflib import Differ
import sys

# ------------------------------------------------------------------

def main():
    lines = sys.stdin.readlines()
    d = Differ()
    diffs = list(d.compare(lines[::2], lines[1::2]))
    sys.stdout.writelines(diffs)

# ------------------------------------------------------------------

if __name__ == '__main__':
    main()
