#!/usr/bin/env python
'''
Some functions for converting numbers to and from different
bitwise representations
'''

# --------------------------------------------------------------------------- #

from __future__ import absolute_import, division, with_statement

import math
import optparse
import logging

REPRESENTATIONS = ('hex', 'bin', 'signed', 'unsigned', 'ascii')

# --------------------------------------------------------------------------- #

def main():
    (opts, args) = getopts()
    fmt = ' '.join(['{{{0}:<13}}'.format(ii)
                    for ii in range(len(REPRESENTATIONS))])
    print fmt.format(*REPRESENTATIONS)
    for arg in args:
        print fmt.format(*(c[1]
                           for c in conv(arg, fr=opts.fr, bits=opts.bits)))

def getopts():
    parser = optparse.OptionParser()
    parser.add_option('--bits', type=int)
    parser.add_option('--fr')
    for rep in REPRESENTATIONS:
        parser.add_option('--'+rep, action='store_true')
    parser.add_option('--verbose',  action='store_true')
    (opts, args) = parser.parse_args()
    if opts.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    for rep in REPRESENTATIONS:
        if getattr(opts, rep):
            opts.fr = rep
    return (opts, args)

# --------------------------------------------------------------------------- #

def signed(num, bits=None, rev=False):
    """
    >>> signed(127)
    127
    >>> signed(126)
    126
    >>> signed(2)
    2
    >>> signed(1)
    1
    >>> signed(0)
    0
    >>> signed(255)
    -1
    >>> signed(254)
    -2
    >>> signed(130)
    -126
    >>> signed(129)
    -127
    >>> signed(128)
    -128
    >>> signed(int('ff', 16))
    -1
    >>> signed(int('ff', 16), bits=32)
    255
    >>> signed(int('ffff', 16))
    -1
    >>> signed(4, rev=True)
    4
    >>> signed(-5, rev=True)
    251
    >>> all(signed(signed(x), rev=True) == x
    ...     for x in (0, 1, 2, 126, 127))
    True
    >>> signed(signed(255), rev=True)
    255
    >>> signed(signed(254), rev=True)
    254
    >>> signed(signed(130), rev=True)
    130
    >>> signed(signed(129), rev=True)
    129
    >>> signed(signed(128), rev=True)
    128
    >>> signed(signed(65535), rev=True)
    255
    >>> signed(signed(65535), bits=16, rev=True)
    65535
    """
    if bits is None:
        # Number of bits in the number, rounded up to the nearest
        # multiple of 8 (assuming the number is in bytes)
        bits = 8 * int(math.ceil((len(bin(abs(num))) - 2) / 8.0))
        logging.debug("Bits for %s: %s", num, bits)

    if rev:
        if num >= 0:
            return num
        else:
            return int(math.pow(2, bits)) - abs(num)

    mask = 1 << (bits-1)
    logging.debug("Mask for %s: %s", num, mask)

    if (num & mask):
        # You can think of 2s complement as being just like
        # binary, except the high bit is negative instead of
        # positive.  So to get it, take the binary numer and
        # subtract off the value of the high bit twice.
        num = num - mask - mask

    return num

def guess_rep(num):
    """
    >>> guess_rep(255)
    'unsigned'
    >>> guess_rep('255')
    'unsigned'
    >>> guess_rep(-5)
    'signed'
    >>> guess_rep('-5')
    'signed'
    >>> guess_rep('ff')
    'hex'
    >>> guess_rep('111')
    'bin'
    >>> guess_rep(-1)
    'signed'
    >>> guess_rep('-1')
    'signed'
    """
    try:
        if int(num, 2) > 0:
            return 'bin'
    except TypeError:
        pass
    except ValueError:
        pass
    try:
        return 'unsigned' if int(num) >= 0 else 'signed'
    except ValueError:
        pass
    try:
        int(num, 16)
        return 'hex'
    except ValueError:
        pass
    return 'ascii'

def to_unsigned(num, rep, bits=None):
    """
    >>> to_unsigned(255, 'unsigned')
    255
    >>> to_unsigned('255', 'unsigned')
    255
    >>> to_unsigned(-5, 'signed')
    251
    >>> to_unsigned('-5', 'signed')
    251
    >>> to_unsigned('ff', 'hex')
    255
    >>> to_unsigned('111', 'bin')
    7
    """
    if rep == 'bin':
        return int(num, 2)
    elif rep == 'hex':
        return int(num, 16)
    elif rep == 'signed':
        return signed(int(num), bits=bits, rev=True)
    elif rep == 'unsigned':
        return int(num)
    elif rep == 'ascii':
        return ord(num)
    raise ValueError("Unknown representation {0}".format(rep))

def from_unsigned(num, rep, bits=None):
    """
    >>> from_unsigned(255, 'unsigned')
    255
    >>> from_unsigned(251, 'signed')
    -5
    >>> from_unsigned(255, 'hex')
    '0xff'
    >>> from_unsigned(7, 'bin')
    '0b111'
    """
    if rep == 'bin':
        return bin(num)
    elif rep == 'hex':
        return hex(num)
    elif rep == 'signed':
        return signed(num, bits=bits)
    elif rep == 'unsigned':
        return num
    elif rep == 'ascii':
        return chr(num)
    raise ValueError("Unknown representation {0}".format(rep))

def conv(num, fr=None, to='all', bits=None):
    """
    convert between
     o byte     = a hex representation
     o unsigned = an int, reading the bits as unsigned
     o signed   = an int, reading the bits as twos complement

    >>> conv(124)
    (('hex', '0x7c'), ('bin', '0b1111100'), ('signed', 124), ('unsigned', 124), ('ascii', '|'))

    >>> conv('124')
    (('hex', '0x7c'), ('bin', '0b1111100'), ('signed', 124), ('unsigned', 124), ('ascii', '|'))

    >>> conv(-5)
    (('hex', '0xfb'), ('bin', '0b11111011'), ('signed', -5), ('unsigned', 251), ('ascii', '\\xfb'))

    >>> conv('-5')
    (('hex', '0xfb'), ('bin', '0b11111011'), ('signed', -5), ('unsigned', 251), ('ascii', '\\xfb'))

    >>> conv('ff')
    (('hex', '0xff'), ('bin', '0b11111111'), ('signed', -1), ('unsigned', 255), ('ascii', '\\xff'))
    """
    if fr is None:
        fr = guess_rep(num)
        logging.debug("Rep for %s: %s", num, fr)
    fr = fr.lower()
    to = to.lower()
    if fr.lower() not in REPRESENTATIONS:
        raise ValueError("Unrecognized fr representation {0}, "
                         "should be one of {1}".format(
                             fr, REPRESENTATIONS))
    if to.lower() not in REPRESENTATIONS + ('all',):
        raise ValueError("Unrecognized to representation {0}, "
                         "should be one of {1}".format(
                             to, REPRESENTATIONS))
    uns = to_unsigned(num, fr, bits=bits)
    logging.debug("Unsigned for %s: %s", num, uns)
    if to == 'all':
        return tuple((r, from_unsigned(uns, r, bits=bits))
                     for r in REPRESENTATIONS)
    else:
        return from_unsigned(uns, to, bits=bits)

# --------------------------------------------------------------------------- #

if __name__ == "__main__":
    main()

