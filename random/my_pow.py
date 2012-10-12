#!/usr/bin/env python
'''
Write code to raise x to the power of y in the most efficient way possible.

Assume x is a float, y is an integer.
'''

def my_pow(x, y):
    '''
    Raise x to the power of y via repeated squaring.

    x should be a float
    y should be an integer

    >>> my_pow(2, 0)
    1.0
    >>> my_pow(2, 1)
    2.0
    >>> my_pow(2, 2)
    4.0
    >>> my_pow(2, 3)
    8.0
    >>> my_pow(2, 4)
    16.0
    >>> my_pow(2, 5)
    32.0
    >>> my_pow(2, 6)
    64.0
    >>> my_pow(2, -1)
    0.5
    >>> my_pow(2, -2)
    0.25
    >>> my_pow(2, -3)
    0.125
    >>> my_pow(2, -4)
    0.0625
    >>> my_pow(3, 15)
    14348907.0
    >>> my_pow(5, -2)
    0.040000000000000001
    >>> my_pow(12, 5)
    248832.0
    '''
    # ensure that x is a float
    x = float(x)
    # ensure that y is an integer
    y = int(y)

    if y == 0:
        return 1.0

    if x == 0 and y < 0:
        raise ZeroDivisionError('%s cannot be raised to a negative power' % x);

    recip = False
    if y < 0:
        y = -y
        recip = True

    #
    # To be efficient, we want to use repeated squaring.  For example,
    # we can calculate x^8 with x=x*x three times, instead of
    # res=res*8 eight times.
    #
    # So we want to decompose y into powers of 2.  One way to do this
    # is to think of y in its binary representation.
    # For example:
    #   10 = 1010  =>  x^10 = x^8       * x^2
    #   15 = 1111  =>  x^15 = x^8 * x^4 * x^2 * x^1
    # Each place value in the binary representation means we need to
    # multiply that power of 2
    #
    result = 1.0
    while y > 0:
        if y % 2 == 1:
            # check for integer overflow?
            result *= x
        # check for integer overflow?
        x = x*x
        # It's ok that this rounds down.  This is equivalent to a
        # right-shift
        y = y/2

    if recip:
        result = 1.0 / result

    return result

def main():
    import doctest
    doctest.testmod()

    for x in range(-5, 5):
        for y in range(-5, 5):
            if x == 0 and y < 0:
                continue
            if my_pow(x, y) != pow(x, y):
                print "Failed  for %s %s" % (x, y)
            else:
                pass
                #print "Success for %s %s" % (x, y)

if __name__ == "__main__":
    main()

