#!/usr/bin/env python
"""
Read in tabular data and perform sql queries on them
"""

# --------------------------------------------------------------------
from __future__ import absolute_import, division, with_statement

import logging
import optparse
import re
import shlex
import sqlite3
import subprocess

# --------------------------------------------------------------------

def main():
    (opts, args) = getopts()

    db = sqlite3.connect(':memory:')
    cursor = db.cursor()

    make_tables(db, cursor, opts.file, read_file)
    make_tables(db, cursor, opts.cmd, read_command)

    for query in args:
        cursor.execute(query)
        data = cursor.fetchall()
        print ' '.join(d[0] for d in cursor.description)
        for row in data:
            print ' '.join(str(v) for v in row)

# --------------------------------------------------------------------

def getopts():
    """
    Parse command-line options
    """
    parser = optparse.OptionParser()
    parser.add_option('--verbose',
                      action='store_true',
                      help='Logging Level DEBUG')
    parser.add_option('--file',
                      action='append',
                      help='file to make into a table')
    parser.add_option('--cmd',
                      action='append',
                      help='command to make into a table')
    parser.add_option('--schema',
                      action='store_true',
                      help='just show the schemas of the tables')
    opts, args = parser.parse_args()

    if opts.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    if opts.schema:
        args.insert(0, 'SELECT name, sql FROM sqlite_master')

    return (opts, args)

# --------------------------------------------------------------------

def make_tables(db, cursor, tables, read_cmd):
    if tables is None:
        return
    for table_info in tables:
        (name, table) = table_info.split('=')
        (header, data) = read_cmd(table)
        make_one_table(db, cursor, name, header, data)

def read_file(filename):
    with open(filename) as f:
        return read_lines(f)

def read_lines(lines):
    header = None
    data = []
    for line in lines:
        fields = re.split('(?<!\\\)\s+', line.strip())
        if line.startswith('#@desc') and header is None:
            header = fields[1:]
            continue
        if line.startswith('#'):
            continue
        if header is None:
            header = fields
        else:
            data.append(fields)
    if header is None:
        header = []
    return (header, data)

def read_command(command):
    logging.info(command)
    proc = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE)
    return read_lines(proc.communicate()[0].splitlines())

def guess_type(value):
    for (pytype, sqltype) in ((int, 'INTEGER'),
                              (float, 'FLOAT')):
        try:
            pytype(value)
            return sqltype
        except ValueError:
            pass
    return 'TEXT'

def make_one_table(db, cursor, name, header, data):
    command = ('CREATE TABLE {name} ({cols});'.
               format(name=name,
                      cols=', '.join("'{0}' {1}".
                                     format(h, guess_type(d))
                                     for (h, d) in zip(header, data[0]))))
    logging.info(command)
    cursor.execute(command)
    for row in data:
        # In case the header appears to have more columns than the rows
        trunc = row[:len(header)]
        command = ('INSERT INTO {0} VALUES ({1});'.
                   format(name,
                          ', '.join('?' for v in trunc)))
        logging.info("Running '{0}' with '{1}'".format(command, trunc))
        cursor.execute(command, trunc)
    db.commit()

# --------------------------------------------------------------------

if __name__ == "__main__":
    main()
