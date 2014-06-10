#!/usr/bin/env python
#
# When executed, this script prints itself
# printme.py | diff - printme.py
#

def printtwice(string):
    string += "'" + "'" + "'"
    print string + string + ")"

printtwice('''#!/usr/bin/env python
#
# When executed, this script prints itself
# printme.py | diff - printme.py
#

def printtwice(string):
    string += "'" + "'" + "'"
    print string + string + ")"

printtwice(''')
