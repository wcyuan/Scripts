def num_string(length):
  """Returns a numbered line.
  
  >>> print(num_string(24))
  012345678901234567890123
  0         1         2
  """
  import math
  base = 10
  lines = []
  for ndigit in range(int(math.log10(length)) + 1):
    interval = int(math.pow(base, ndigit))
    lines.append(''.join(
        (str(n % base) + (' ' * (interval-1)))
        for n in range((length - 1) // interval + 1)))
  return '\n'.join(lines)
