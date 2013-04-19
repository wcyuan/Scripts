def num_to_english(num):
    '''
    Write a function that takes a number like 1499123 and returns the
    number represented in English words - "one million four hundred
    ninety nine thousand one hundred twenty three".

    >>> num_to_english(4)
    'four'
    >>> num_to_english(1151)
    'one thousand one hundred fifty one'
    >>> num_to_english(-19)
    'negative nineteen'
    >>> num_to_english(0)
    'zero'
    >>> num_to_english(1325915)
    'one million three hundred twenty five thousand nine hundred fifteen'
    >>> num_to_english(-13053020515)
    'negative thirteen billion fifty three million twenty thousand five hundred fifteen'
    '''
    num_names = [(1e15, 'quadrillion'),
                 (1e12, 'trillion'),
                 (1e9,  'billion'),
                 (1e6,  'million'),
                 (1e3,  'thousand'),
                 (100,  'hundred'),
                 (90,   'ninety'),
                 (80,   'eighty'),
                 (70,   'seventy'),
                 (60,   'sixty'),
                 (50,   'fifty'),
                 (40,   'forty'),
                 (30,   'thirty'),
                 (20,   'twenty'),
                 (19,   'nineteen'),
                 (18,   'eighteen'),
                 (17,   'seventeen'),
                 (16,   'sixteen'),
                 (15,   'fifteen'),
                 (14,   'fourteen'),
                 (13,   'thirteen'),
                 (12,   'twelve'),
                 (11,   'eleven'),
                 (10,   'ten'),
                 (9,    'nine'),
                 (8,    'eight'),
                 (7,    'seven'),
                 (6,    'six'),
                 (5,    'five'),
                 (4,    'four'),
                 (3,    'three'),
                 (2,    'two'),
                 (1,    'one')]
    if num < 0:
        return 'negative ' + num_to_english(abs(num))
    if num == 0:
        return 'zero'
    parts = []
    while num > 0:
        for (val, name) in num_names:
            if num >= val:
                sub = int(num / val)
                if val >= 100:
                    parts.append(num_to_english(sub))
                parts.append(name)
                num = num % val
                break
        else:
            raise AssertionError("No match for {0}!".format(num))
    return ' '.join(parts)

if __name__ == "__main__":
    import doctest
    doctest.testmod(verbose=True)
