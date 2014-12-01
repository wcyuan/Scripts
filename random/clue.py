#!/usr/bin/env python
"""
A simple script to play
http://en.wikipedia.org/wiki/Cluedo
"""

# --------------------------------------------------------------------------- #

from __future__ import absolute_import, division, with_statement

import logging
import optparse
import random

logging.basicConfig(format='[%(asctime)s '
                    '%(funcName)s:%(lineno)s %(levelname)-5s] '
                    '%(message)s')

# --------------------------------------------------------------------------- #

SUSPECTS = (
    "Miss Scarlett",
    "Professor Plum",
    "Mrs. Peacock",
    "Mr. Green",
    "Colonel Mustard",
    "Mrs. White")

WEAPONS = (
    "Candlestick",
    "Knife",
    "Lead Pipe",
    "Revolver",
    "Rope",
    "Wrench")

ROOMS = (
    "Kitchen",
    "Ballroom",
    "Conservatory",
    "Dining Room",
    "Billiard Room",
    "Library",
    "Lounge",
    "Hall",
    "Study")

# --------------------------------------------------------------------------- #

DEFAULT_NPLAYERS = 4

# --------------------------------------------------------------------------- #

def main():
    (opts, args) = getopts()
    play_game(nplayers=opts.nplayers)
    

def getopts():
    parser = optparse.OptionParser()
    parser.add_option('--verbose',  action='store_true')
    parser.add_option('--nplayers',  type='int', default=DEFAULT_NPLAYERS)
    (opts, args) = parser.parse_args()
    if opts.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    return (opts, args)

# --------------------------------------------------------------------------- #

def choose(lst):
    ii = random.randrange(len(lst))
    return (lst[ii], lst[:ii] + lst[ii+1:])

def shuffle(lst):
    # make a copy, make sure it's mutable
    lst = list(lst)
    length = len(lst)
    for ii in xrange(length):
        switchwith = random.randrange(length)
        lst[ii], lst[switchwith] = lst[switchwith], lst[ii]
    return lst

def deal(nplayers=DEFAULT_NPLAYERS, suspects=SUSPECTS, weapons=WEAPONS, rooms=ROOMS):
    (suspect, rest_suspects) = choose(suspects)
    (weapon, rest_weapons) = choose(weapons)
    (room, rest_rooms) = choose(rooms)
    answer = (suspect, weapon, room)
    deck = shuffle(rest_suspects + rest_weapons + rest_rooms)
    hands = tuple([] for _ in xrange(nplayers))
    for ii, card in enumerate(deck):
        hands[ii % nplayers].append(card)
    return (answer, hands)

def get_guess(name, lst):
    while True:
        val = raw_input("Enter {0}: ".format(name))
        if val in lst:
            return val
        print "Invalid {0} '{1}'.  Must be one of {2}".format(
            name, val, lst)

def check_guess(suspect, weapon, room, answer, hands):
    if (suspect, weapon, room) == answer:
        return True
    denials = [(card, player+1)
               for player, hand in enumerate(hands[1:])
               for card in hand
               if card in (suspect, weapon, room)]
    if len(denials) == 0:
        print "No one can prove that guess wrong"
    else:
        (card, player) = random.choice(denials)
        print "Player {0} has card {1}".format(player, card)

    return False

def print_hand(hand,
               suspects=SUSPECTS,
               weapons=WEAPONS, 
               rooms=ROOMS):
    for (name, lst) in (("Suspects", suspects),
                        ("Weapons", weapons),
                        ("Rooms", rooms)):
        vals = sorted(c for c in hand if c in lst)
        print "{0}: {1}".format(name, vals)

def play_game(nplayers=DEFAULT_NPLAYERS,
              suspects=SUSPECTS,
              weapons=WEAPONS, 
              rooms=ROOMS):
    (answer, hands) = deal(nplayers, suspects, weapons, rooms)
    while True:
        print_hand(hands[0], suspects, weapons, rooms)
        print "Guess -- "
        suspect = get_guess("Suspect", suspects)
        weapon = get_guess("Weapon", weapons)
        room = get_guess("Room", rooms)
        if check_guess(suspect, weapon, room, answer, hands):
            print "You got it!"
            break

# --------------------------------------------------------------------------- #

if __name__ == "__main__":
    main()

# --------------------------------------------------------------------------- #
