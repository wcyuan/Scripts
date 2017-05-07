#!/usr/bin/env python

"""Checks TMNT compliance.  https://xkcd.com/1412/
Written by jktomer
"""

import sys

class S(object):
  """Enum classifies each syllable: it may be stressed or unstressed."""
  no = 0
  yes = 1
  # Just one syllable in this word. May be stressed when it is spoken.
  single = 2

CMUDICT = 'cmudict.0.7a'


# Fix some dictionary entries.
OVERRIDES = {
    'ASYNC': [S.yes, S.no],  # Not contained in dictionary.
    'BOOLEAN': [S.yes, S.no],  # Was no,yes,no; this is better.
    'EXEC': [S.no, S.yes],  # Was yes,no. Don't mispronounce it.
    'FETCHER': [S.yes, S.no],  # Fetcher's not in dictionary!?
    'FIREBASE': [S.yes, S.no, S.yes],  # This was missing; now it isn't.
    'ID': [S.no, S.yes],  # Not how Sigmund Freud would say it.
    'IMPL': [S.yes, S.no],  # Not a real word (rhymes with "simple").
    'IP': [S.no, S.yes],  # Said as if you're urinating.
    'SHRINKER': [S.yes, S.no],  # Dictionary overlooked it.
}


def load_dictionary():
  """Loads pronunciation word list.

  Returns:
    Dictionary indicating syllables with stress or no stress. Every uppercase
    word maps to its own list of booleans, where a True means that a syllable
    is stressed and False means it is unstressed.
  """
  stresses_by_word = {}
  with open(CMUDICT) as fd:
    for line in fd:
      if not line[0].isalpha():
        continue
      word, pronunciation = line.split(' ', 1)
      stresses = [(S.yes if char == '1' or char == '2' else S.no)
                  for char in pronunciation if char.isdigit()]
      if len(stresses) == 1:
        # Words with just one syllable are stressed or not; depends on context.
        stresses = [S.single]
      stresses_by_word[word] = stresses

  stresses_by_word.update(OVERRIDES)
  # I refuse to touch this comment. Jacob's gone and can't update it. Maybe
  # lewismark will do it.
  ## TODO(jacobly): some two-syllable words are listed as [primary, unstressed]
  ## and others as [primary, secondary], which we count as [S.yes, S.yes].
  ## It's tempting to special-case this as [S.yes, S.no].
  return stresses_by_word


def split_camelcase(class_name):
  """CamelCase to list converter: classname words are separated."""
  words = []
  start_idx = 0
  for i, char in list(enumerate(class_name))[1:]:
    if char.isupper():
      words.append(class_name[start_idx:i])
      start_idx = i
  words.append(class_name[start_idx:])
  return words


def is_tmnt(stresses_by_word, in_string):
  """Is it TMNT-compliant?"""
  words = [s for word in in_string.split() for s in split_camelcase(word)]

  stresses = []
  for word in words:
    word = word.upper()
    if word not in stresses_by_word:
      return False
    stresses.extend(stresses_by_word[word])

  # If a syllable is stressed, it's fine in an unstressed location,
  # but vice-versa breaks the rhythm.
  # Words with just a single syllable can fill the first position, but in any
  # other spot we can't tell if they're stressed or not, see?
  return (len(stresses) == 8 and
          (stresses[0] == S.yes or stresses[0] == S.single) and
          stresses[2] == S.yes and
          stresses[4] == S.yes and
          stresses[6] == S.yes)


def main():
  """Checks the whole repository for the Ninja Turtle rhythm."""
  stresses = load_dictionary()
  for line in sys.stdin:
    line = line.strip()
    if not line:
      continue
    if is_tmnt(stresses, line):
      print line


if __name__ == '__main__':
  main()
  
