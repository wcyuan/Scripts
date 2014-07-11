#!/usr/bin/env python
'''
http://www.datagenetics.com/blog/may12012/index.html

------------------------------------------------------------------

1. Band around the World

Imagine that you equipped the Earth with tightly fitting steel
belt running all around the equator (assume, for this puzzle, that
the Earth is a perfect sphere). The belt fights taut and snug.

Now, imagine you took a saw, cut the belt, added an extra 2 meter
section of belt, and welded it back together. The slightly-longer
belt will now be a little bit loose, and stand proud of the
surface of the Earth all the way around.

[For those not familiar with the Metric system, 2 meters is just
over six and half feet.]

Question: How big will the gap between the planet and the band be?

Will the gap be big enough for a couple of air-molecules to pass
under? Big enough to slide a playing card under? Big enough to
slide your hand under? How about a telephone directory? Would it
be big enough for a cat to crawl under? How about a person?

------------------

Intuition: it hardly leaves any gap

------------------

R = radius of Earth
C = circumference of Earth = 2 * pi * R
B = length of band = 2 * pi * R + 2
X = radius of bank = R + (1 meter/pi) = R + about 2 feet

So big enough for a cat, but not a person.

------------------------------------------------------------------

2. Giant Jelly

Imagine you have giant jelly. The jelly weighs 100 pounds, and is
99% water by weight.

You leave the jelly out, and let water evaporate from the jelly
until it reaches 98% water by weight.

Question: How much does the jelly now weigh?

------------------

Intuition: almost the same as before

------------------

In the beginning:
- 99lb water, 1 lb other

After evaporation (x is the amount of water)
- x / (x + 1lb) = .98
- x = .98 x + .98lb
- .02x = .98lb
- x = .98 / 0.02 = 49 lbs

So total weight = 50lbs

------------------------------------------------------------------

3. Second Black Ace

Someone hands you a deck of cards which you thoroughly
shuffle. Next, you start to deal them, face-up, counting the cards
as you go. ?One, Two, Three ??

The aim is to predict what the count will be when you encounter
the second black Ace in the deck.

Question: If you had to select one position before you started to
deal, what number would you select that maximizes your chance of
guessing the location of the second black Ace?

------------------

Intuition: about 2/3 through the deck

------------------

There are 52! ways of ordering the deck

How many of those cases have the first black ace in:
position 1: 2*51! = 51*2*50!
position 2: 50*2*50!
- note that this is smaller than the number of cases where it is in
the first position because 50 < 51
position 3: 50*49*2*49! = 49*2*50!
position 4: 50*49*48*2*48! = 48*2*50!
position n: (52-n)*2*50!

Sanity check: is sum (for n = 1 to 52) {(52-n) * 2 * (50)!} = 52!?

= 2*50!*sum ( for n = 1 to 52 ) { 52 - n }
note that sum ( for n = 1 to 52 ) { 52 - n } = sum ( for n = 1 to 52 ) { n }
= 2*50!*(52 * 51 / 2)

YES!

So the most likely position for the first black ace is the 1st
position!

How many cases are there where the second black ace is in:

position 1: none
position 2: 2*1*50! = 2 * 50!
position 3: 2*50*1*49! + 50*2*1*49! = 2*50*1*49! * 2 = 4 * 50!
position 4:
2*50*49*1*48! + 50*2*49*1*48! + 2*50*49*1*48! = 2*50*49*1*48! * 3 = 6 * 50!

position n: 2 * (n-1) * 50!

So the most likely position for the second black ace is the last
position!

Sanity check: is sum ( for n = 1 to 52 ) { 2 * (n-1) * 50! } = 52!?

= 2 * 50! * sum ( for n = 1 to 52 ) { n - 1 } = 2 * 50! (52 * 51 / 2) = 52!

Yes!

------------------------------------------------------------------

4. Aces in Bridge Hands

Someone deals you a bridge hand (13 cards from a regular deck of 52
cards). You look at the hand and notice you have an Ace and say "I
have an Ace". What is the probability that you have another Ace?

The cards are collected and different hand is dealt. This time you
look at your hand and state "I have the Ace of Spades" (which is
true), what is the probability, this time, that you have another Ace?

Question: Is the probability in the second case the same as before, a
lower probability, or a higher probability?

------------------

Intuition: about the same

But because I've heard the girl named florida question, I'd say the
probability w/ ace of spades is higher.

For the "I have the ace of spades" part, the implication is that if
you are dealt the ace of spades, you will say it, but if are not dealt
the ace of spades you won't say anything

------------------

Define:
AS = event of the ace of spades in your hand and no other aces
ASA = event of the ace of spades in your hand and exactly 1 other ace
ASAA = event of the ace of spades in your hand and exactly 2 other aces
ASAAA = event of the ace of spades in your hand and exactly 3 other aces
AS+ = event of the ace of spades in your hand and any number of other aces
A = event of exactly 1 ace in your hand
A+ = event of at least 1 ace in your hand
AA = event of exactly 2 aces in your hand
AA+ = event of at least 2 aces in your hand
etc.
P(A) = prob of having exactly 1 ace in your hand
P(A+) = prob of having at least 1 ace in your hand
etc.

note, P(AS) < P(A+) and ASAAA = AAAA

Question is to compare P(AA+|A+) and P(AA+|AS+)

Suppose you have exactly 1 ace in your hand.  What is the probability
that it's the ace of spades?
P(AS|A) = P(AS) / P(A) = 1/4
P(ASA|AA) = P(ASA) / P(AA) = 2/4
P(ASAA|AAA) = P(ASAA) / P(AAA) = 3/4
P(ASAAA|AAAA) = P(ASAAA) / P(AAAA) = 1

P(A+) = P(A) + P(AA) + P(AAA) + P(AAAA)
P(AA+) = P(AA) + P(AAA) + P(AAAA)
P(AA+|A+) = (P(AA) + P(AAA) + P(AAAA)) / (P(A) + P(AA) + P(AAA) + P(AAAA))

P(AA+|AS+) = (P(ASA) + P(ASAA) + P(AAAA)) / (P(AS) + P(ASA) + P(ASAA) + P(AAAA))
= (.5*P(AA) + .75*P(AAA) + P(AAAA)) / (.25*P(A) + .5*P(AA) + .75*P(AAA) + P(AAAA))

So which is bigger?
P(AA+|A+) = (P(AA) + P(AAA) + P(AAAA)) / (P(A) + P(AA) + P(AAA) + P(AAAA))

or

P(AA+|AS+) = = (.5*P(AA) + .75*P(AAA) + P(AAAA)) / (.25*P(A) + .5*P(AA) + .75*P(AAA) + P(AAAA))

to put it another way, which is smaller:

P(A) / (P(A) + P(AA) + P(AAA) + P(AAAA))

or

.25*P(A) / (.25*P(A) + .5*P(AA) + .75*P(AAA) + P(AAAA))

to put it another way, which is bigger:

P(A+) = (P(A) + P(AA) + P(AAA) + P(AAAA))

or

4*P(AS+) = 4 * (.25*P(A) + .5*P(AA) + .75*P(AAA) + P(AAAA))

         = P(A) + 2*P(AA) + 3*P(AAA) + 4*P(AAAA)

Clearly that's bigger than just P(A) + P(AA) + P(AAA) + P(AAAA)

So P(AA+|AS+) > P(AA+|A+)

Put it another way: In the first case, an event is trigger each time
you have 1, 2, 3, or 4 aces.  In the second case, an event is
triggered 25% of the time if you have 1 ace, 50% of the time if you
have 2 aces, 75% of the time if you have three aces, and every time if
you have 4 aces.  So if the second event triggers, it weighs the cases
with more aces more highly.

'''
