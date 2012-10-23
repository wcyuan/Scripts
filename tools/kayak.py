#!/usr/bin/env python
"""
kayak.py <csv-file>

filter out any flights that aren't the fewest number of stops

group flights by price

within each price, show the options for each leg.

"""

from csv      import reader        as csvreader
from optparse import OptionParser
from logging  import warning
from operator import attrgetter

# Expected fields:
#
# RECORD
# PRICE
# STOPS
# DURATION
# DEPART
# DEPART DATE
# DEPART TIME
# ARRIVE
# ARRIVE DATE
# ARRIVE TIME
# AIRLINE
# FLIGHT
# CLASS
# EQUIPMENT

def main():
    """
    """
    opts, args = getopts()

    trips = read_file(args[0])
    trips = filter_stops(trips)
    trips = filter_price(trips)
    output_trips(trips)

def getopts():
    """
    Parse the command-line options
    """
    parser = OptionParser()
    opts, args = parser.parse_args()
    return (opts, args)

class Trip(object):
    """
    A trip is basically a list of legs.
    """
    def __init__(self, record):
        self.record = record
        self.price = None
        self.legs = []

    @classmethod
    def time_to_minutes(cls, time):
        return (int(time) / 100) * 60 + (int(time) % 100)

    @classmethod
    def minutes_to_time(cls, minutes):
        while minutes < 0:
            minutes += 24*60
        return "%2d:%02d" % ((minutes/60, minutes%60))

    @classmethod
    def leg_duration(cls, leg):
        depart=leg['DEPART TIME']
        arrive=leg['ARRIVE TIME']
        return cls.minutes_to_time(cls.time_to_minutes(arrive) -
                                    cls.time_to_minutes(depart))

    @classmethod
    def leg_str(cls, leg):
        return '%s-%s  %s-%s (%s stops %5s)' % (
                leg['DEPART TIME'],
                leg['ARRIVE TIME'],
                leg['DEPART'],
                leg['ARRIVE'],
                leg['STOPS'],
                cls.leg_duration(leg)
                )

    def __str__(self):
        return '%5s %6s | %s' % (
            self.record,
            "$" + str(self.price),
            ' | '.join(self.leg_str(l) for l in self.legs))

    @property
    def leg_times(self):
        '''
        for sorting
        '''
        return '|'.join('-'.join((leg['DEPART TIME'],
                                  leg['ARRIVE TIME'],
                                  leg['DEPART'],
                                  leg['ARRIVE']))
                        for leg in self.legs)

    def add_leg(self, leg):
        self.legs.append(leg)
        leg_price = int(leg['PRICE'][1:])
        if self.price is None:
            self.price = leg_price
        elif self.price != leg_price:
            warning("Different prices (%s != %s) for record %s" %
                    (self.record, self.price, leg_price))

def read_file(csvfilename):
    """
    Read the csv file.  Each line of the file is a leg.  A trip is N
    consecutive rows.  All the legs in a trip will have the same
    RECORD id (and PRICE and DURATION, which is the length of the
    total trip in minutes).
    """
    trips={}
    with open(csvfilename) as csvfile:
        csvdata = csvreader(csvfile)
        header=None
        for row in csvdata:
            if len(row) == 0:
                continue
            if row[0] == 'RECORD':
                header=row
            else:
                # this row is the leg of a trip
                leg = {}
                for (fld, val) in zip(header, row):
                    leg[fld] = val
                if leg['RECORD'] not in trips:
                    trips[leg['RECORD']] = Trip(leg['RECORD'])
                trips[leg['RECORD']].add_leg(leg)
    return trips

def filter_stops(trips):
    """
    filter out all but the trips with the minimum stops
    """
    min_stops = []
    for trip in trips:
        for leg_id in range(len(trips[trip].legs)):
            nstops = int(trips[trip].legs[leg_id]['STOPS'])
            if leg_id >= len(min_stops):
                min_stops.extend([None] * (leg_id - len(min_stops) + 1))
            if (min_stops[leg_id] is None or
                nstops < min_stops[leg_id]):
                min_stops[leg_id] = nstops

    new_trips = {}
    for trip in trips:
        for leg_id in range(len(trips[trip].legs)):
            if int(trips[trip].legs[leg_id]['STOPS']) == min_stops[leg_id]:
                new_trips[trip] = trips[trip]

    return new_trips

def filter_price(trips):
    """
    sort by price

    show at least 20 flights

    if there are more than 20 flights to show, then after the first
    20, only show the flight if it's within $300 of the minimum price
    """
    by_price = sorted(trips.values(), key=attrgetter('price', 'leg_times'))
    if len(by_price) > 20:
        min_price = by_price[0].price
        for idx in range(20, len(by_price)):
            if by_price[idx].price > min_price+300:
                return by_price[:idx]

    return by_price

def output_trips(trips):
    """
    group trips by price
    """
    lastprice = None
    for trip in trips:
        if lastprice is not None and lastprice != trip.price:
            print
        print trip
        lastprice = trip.price

if __name__ == "__main__":
    main()
