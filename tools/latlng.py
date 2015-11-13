#!/usr/bin/env python
"""Calculate the distance between two latlngs

Uses the haversine formula.  Stolen from
http://andrew.hedges.name/experiments/haversine/

Note: this formula does not take into account the non-spheroidal
(ellipsoidal) shape of the Earth. It will tend to overestimate
trans-polar distances and underestimate trans-equatorial
distances. The values used for the radius of the Earth (3961 miles &
6373 km) are optimized for locations around 39 degrees from the
equator (roughly the Latitude of Washington, DC, USA).

"""

# --------------------------------------------------------------------------- #

from __future__ import absolute_import, division, with_statement

import logging
import math
import optparse

# --------------------------------------------------------------------------- #

logging.basicConfig(format="[%(asctime)s "
                    "%(funcName)s:%(lineno)s %(levelname)-5s] "
                    "%(message)s")

KM_EARTH_RADIUS = 6373.0
MILES_EARTH_RADIUS = 3961.0

# --------------------------------------------------------------------------- #


def main():
  (opts, args) = getopts()

  if not args:
    return

  points = [LatLng(arg, opts.input_type) for arg in args]
  source = points[0]
  types = ["degrees", "radians", "signed_e7", "unsigned_e7"]
  lines = []
  # header
  lines.append(types + ["distance(m,km)"])
  for point in points:
    line = point.latlng_as(types)
    line.append(haversine(source.latlng_as("degrees"),
                          point.latlng_as("degrees")))
    line = [str(val) for val in line]
    lines.append(line)
  table = make_table(lines)
  print table

def getopts():
  parser = optparse.OptionParser()
  parser.add_option("--degrees", action="store_const",
                    const="degrees", dest="input_type")
  parser.add_option("--radians", action="store_const",
                    const="radians", dest="input_type")
  parser.add_option("--e6", action="store_const",
                    const="signed_e6", dest="input_type")
  parser.add_option("--e7", action="store_const",
                    const="signed_e7", dest="input_type")
  parser.add_option("--verbose", action="store_true")
  parser.add_option("--log_level", help="The level to log at")
  parser.add_option("--no_write",
                    action="store_true",
                    help="Just print commands without running them")
  (opts, args) = parser.parse_args()

  if opts.verbose:
    logat(logging.DEBUG)

  if opts.log_level is not None:
    logat(opts.log_level)

  return (opts, args)


def logat(level):
  if isinstance(level, basestring):
    level = getattr(logging, level.upper())
  logging.getLogger().setLevel(level)
  logging.info("Setting log level to %s", level)

# --------------------------------------------------------------------------- #

def signed(num, bits):
  mask = 1 << (bits-1)
  inum = int(num)
  if (inum & mask):
    # You can think of 2s complement as being just like
    # binary, except the high bit is negative instead of
    # positive.  So to get it, take the binary number and
    # subtract off the value of the high bit twice.
    inum = inum - mask - mask
    return inum
  else:
    return num

def unsigned(num, bits):
  # To go from 2s complement to unsigned bits,
  # for positive numbers, do nothing
  # for negative numbers, invert the bits and add 1
  highbit = 1 << (bits-1)
  num = int(num)
  if (num & highbit):
    num *= -1
    mask = int(pow(2, bits) - 1)
    num ^= mask
    num += 1
  return num

def deg_to_rad(deg):
  return deg * (math.pi / 180)

class LatLng(object):
  def __init__(self, csv_values, input_type=None):
    self.orig = csv_values.strip("(").strip(")")
    self.input_type = input_type
    lat, lng = [float(val) for val in self.orig.split(",", 1)]
    if not input_type:
      input_type = self.guess_input_type([lat, lng])
    self.lat_e7 = self.to_signed_e7(lat, input_type)
    self.lng_e7 = self.to_signed_e7(lng, input_type)

  @classmethod
  def guess_input_type(cls, vals):
    if all(abs(val) < 6 for val in vals):
      return "radians"
    if any(abs(val) > 1e7 for val in vals):
      if any(val < 0 for val in vals):
        return "signed_e7"
      else:
        return "unsigned_e7"
    if any(abs(val) > 1e6 for val in vals):
      if any(val < 0 for val in vals):
        return "signed_e6"
      else:
        return "unsigned_e6"
    if all(abs(val) < 360 for val in vals):
      return "degrees"
    logging.warning("Can't guess input type for %s, using degrees", vals)
    return "degrees"


  @classmethod
  def to_signed_e7(cls, val, input_type):
    """
    to signed e7 values
    """
    orig_val = val
    orig_type = input_type
    if input_type.startswith("unsigned"):
      val = signed(val, 32)
      input_type = input_type[2:]
    if input_type.endswith("e6"):
      val *= 10
      input_type = input_type[:-1] + "7"
    if input_type == "radians":
      val *= (180 / math.pi)
      input_type = "degrees"
    if input_type == "degrees":
      val *= 1e7
      input_type = "signed_e7"
    if input_type != "signed_e7":
      logging.error("Failed to convert %s %s, got to %s %s",
                    orig_val, orig_type, val, input_type)
    return val

  def __repr__(self):
    return 'LatLng({self.lat_e7},{self.lng_e7},"signed_e7")'.format(self=self)

  @classmethod
  def signed_e7_to(cls, val, output_type):
    if output_type.startswith("unsigned"):
      val = unsigned(val, 32)
    if output_type.endswith("e6"):
      val /= 10
    if output_type == "degrees" or output_type == "radians":
      val /= 1e7
    if output_type == "radians":
      val *= (math.pi / 180)
    return val

  @classmethod
  def value_as(cls, val, output_types=None):
    if not output_types:
      output_types = []
    if isinstance(output_types, basestring):
      output_types = [output_types]
    if len(output_types) == 1:
      return cls.signed_e7_to(val, output_types[0])
    else:
      return [cls.signed_e7_to(val, output_type)
              for output_type in output_types]

  def lat_as(self, output_types=None):
    return self.value_as(self.lat_e7, output_types)

  def lng_as(self, output_types=None):
    return self.value_as(self.lng_e7, output_types)

  def latlng_as(self, output_types=None):
    lats = self.lat_as(output_types)
    lngs = self.lng_as(output_types)
    try:
      if len(lats) > 1:
        return zip(lats, lngs)
    except:
      pass
    return lats, lngs

# --------------------------------------------------------------------------- #

def haversine(latlng1, latlng2):
  """
  Computes distance according to the haversine formula
  """
  (lat1, lng1) = latlng1
  (lat2, lng2) = latlng2
  lat1 = deg_to_rad(lat1)
  lng1 = deg_to_rad(lng1)
  lat2 = deg_to_rad(lat2)
  lng2 = deg_to_rad(lng2)
  dlng = lng2 - lng1
  dlat = lat2 - lat1
  a = (math.pow(math.sin(dlat/2.0), 2.0) +
       math.cos(lat1) * math.cos(lat2) * math.pow(math.sin(dlng/2.0), 2.0))
  c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
  d_km = KM_EARTH_RADIUS * c
  d_miles = MILES_EARTH_RADIUS * c
  return (d_km, d_miles)

def deg_to_rad(deg):
  return deg * (math.pi / 180)

# --------------------------------------------------------------------------- #

def make_table(table, delim=' ', ors='\n', left=True):
  import itertools
  transposed = itertools.izip_longest(*table, fillvalue='')
  widths = (max(len(fld) for fld in line) for line in transposed)
  lch = '-' if left else ''
  formats = ['%{0}{1}s'.format(lch, width) for width in widths]
  return ors.join('%s' % delim.join(format % (fld)
                                    for (format, fld) in zip(formats, line))
                  for line in table)

# --------------------------------------------------------------------------- #

if __name__ == "__main__":
  main()

# --------------------------------------------------------------------------- #
