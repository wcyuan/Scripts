#!/usr/bin/env python
"""
from http://www.espenhaug.com/black_scholes.html

No idea if this is correct
"""
# --------------------------------------------------------------------------- #

from math import exp, log, pi, sqrt
import logging
import optparse

logging.basicConfig(format='[%(asctime)s '
                    '%(funcName)s:%(lineno)s %(levelname)-5s] '
                    '%(message)s')


# --------------------------------------------------------------------------- #

def main():
    (opts, _) = getopts()

    print BlackScholes(CallPutFlag=opts.put_call,
                       S=opts.stockprice,
                       X=opts.strike,
                       T=opts.texp,
                       r=opts.riskfree,
                       v=opts.volatility)

def getopts():
    parser = optparse.OptionParser()
    parser.add_option('--verbose',    action='store_true')
    parser.add_option('--put_call',   choices=('c', 'p'))
    parser.add_option('--stockprice', type=float, help='stock price')
    parser.add_option('--strike',     type=float, help='strike price')
    parser.add_option('--riskfree',   type=float,
                      help='risk free interest rate')
    parser.add_option('--volatility', type=float, help='volatility')
    parser.add_option('--texp',       type=float,
                      help='time to expiration in years')
    (opts, args) = parser.parse_args()
    if opts.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    return (opts, args)

# --------------------------------------------------------------------------- #

def cumnorm(X):
    """
    # Cumulative normal distribution
    """
    (a1, a2, a3, a4, a5) = (
        0.31938153, -0.356563782, 1.781477937, -1.821255978, 1.330274429)

    L = abs(X)

    K = 1.0 / (1.0 + 0.2316419 * L)

    w = (1.0 -
         1.0 / sqrt(2 * pi) * exp(-L * L/2.) * (
             a1 * K + a2 * K * K + a3 * pow(K, 3) +
             a4 * pow(K, 4) + a5 * pow(K, 5)))

    if X < 0:
        w = 1.0 - w

    return w


def BlackScholes(CallPutFlag, S, X, T, r, v):
    """
    Compute option price from volatility.

    @param CallPutFlag: either 'c' or 'p'
    @param S: Stock price
    @param X: Strike price
    @param r: annual risk free interest rate
    @param T: time to expiration in years
    @param v: volatility
    """

    d1 = (log(S / X) + (r + v * v / 2.) * T) / (v * sqrt(T))

    d2 = d1 - v * sqrt(T)

    if CallPutFlag=='c':
        return S * cumnorm(d1) - X * exp(-r * T) * cumnorm(d2)
    else:
        return X * exp(-r * T) * cumnorm(-d2) - S * cumnorm(-d1)

# --------------------------------------------------------------------------- #

if __name__ == "__main__":
    main()

# --------------------------------------------------------------------------- #
