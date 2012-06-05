#!/usr/local/bin/perl -w
#
# squash.pl
# @desc:  volleyball vs tennis scoring
#
# Conan Yuan, 20070122
#

=head1 NAME

squash.pl - volleyball vs tennis scoring

=head1 SYNOPSIS

  squash.pl [options] <your_points_to_win> <opp_points_to_win> <prob_win_when_serving> <prob_win_when_receiving>

  Options:
    --help, -?        shows brief help message
    --perldoc         shows full documentation

  See also Getopt::Long for complete standard options list.

=head1 ARGUMENTS

=over

=item I<your_points_to_win>

the number of points you need in order to win

=item I<opp_points_to_win>

the number of points your opponent needs in order
to win

=item I<prob_win_when_serving>

the probability you win the point when you are serving

=item I<prob_win_when_receiving>

the probability you win the point when receiving

=back

=head1 OPTIONS

=over 4

=item I<--help>

Print a brief help message and exit.

=item I<--perldoc>

Print the perldoc page and exit.

=back

=head1 DESCRIPTION

There are two ways to keep track of scoring in squash. Under one
method, (Volleyball Scoring) players can score only when they are
serving. If a player wins a point when receiving, he does not score a
point, but he gets to serve (first serve is determined by a
coinflip). The other method (Tennis Scoring) allows players to score
both when serving and receiving.

=over 4

=item 1.

Suppose you are challenged to a game of squash by a superior player
(i.e., you have <50% shot at winning any individual point). However,
he offers you the choice between tennis scoring and squash
scoring. Which (if either) gives you a greater chance of winning?
Explain your answer intuitively.

Tennis scoring is easier.

Suppose that it's best to 1 point, and that no one starts out with the
serve.  It's sort of like the basketball question.  Tennis style, you
need to win a point.  Volleyball, you need to win two in a row before
your opponent wins two in a row.  Since every time you win, you need
to be "lucky", now you need to be "twice as lucky".

Or, think of it like this.  Let's say there were two games ending X
points to Y points.  In tennis scoring, X won X points and Y won Y
points.  In volleyball scoring, X won X+N points and Y won Y+N points
(off by one, depending on who started with the serve).  So the winner
in volleyball scoring won (X+N)/(X+Y+N+N) of the points.  This number
is closer to 50% than X/(X+Y) is.  So let's say X won, meaning
X/(X+Y) > 50 and so (X+N)/(Y+2N) < X/(X+Y).  That is, in volleyball
scoring, the winner won a smaller percentage of the points.

That means, in the tennis scoring game, the winner won more of the
points than the winner in the volleyball game, but the score was the
same in each.  In the tennis game, the winner had to be more dominant
to get the same score.

=item 2.

Now you are challenged by an equally skilled player (you both have a
50-50 shot at winning any given point). Furthermore you only have to
score (say) 5 points to win the game and he has to score (say) 9 AND
you get the choice between tennis scoring and squash scoring. Which
(if either) gives you a greater chance of winning the game? Explain
your answer intuitively.

=item 3.

Come up with a function psquashwinT() that computes the probability of
winning a game of squash (tennis scoring) as a function of number of
points you must score, number of points your opponent must score, and
probability you win any given point.

=item 4.

Come up with a function psquashwinV() that computes the probability of
winning a game of squash (volleyball scoring) as a function of number
of points you must score, number of points your opponent must score,
probability you will win a given point when serving (ps), and
probability you will win a given point when receiving (pr).

=item 5.

Under what conditions do you prefer to be better at serving than
receiving (ps > pr)?

=item 6.

Given you have some quantity of skill, P, to allocate between ps and
pr, what allocation gives you the greatest chance of winning a given
game? (Assume P < 1. If P > 1, you can just set pr = 1 and never
lose).

=back

=cut

use strict;
use warnings 'all';
use Pod::Usage;

use Getopt::Long;
use Text::Table;

# ----------------------

# default values

# parse command-line options
GetOptions()
    or pod2usage();

# parse script arguments
pod2usage("Wrong number of arguments") unless @ARGV == 4;
my $your_points_to_win      = shift @ARGV;
my $opp_points_to_win       = shift @ARGV;
my $prob_win_when_serving   = shift @ARGV;
my $prob_win_when_receiving = shift @ARGV;

# ----------------------

sub tennis_scoring ( $$$;$ ) {
    my ($your_points_to_win,
	$opp_points_to_win,
	$prob_win) = @_;

    if ($your_points_to_win <= 0) {
	return 1;
    }

    if ($opp_points_to_win <= 0) {
	return 0;
    }

    my @points;
    for (my $your_points = 1; $your_points <= $your_points_to_win; $your_points++) {
	for (my $opp_points = 1; $opp_points <= $opp_points_to_win; $opp_points++) {
	    my ($prob_if_win, $prob_if_lose);
	    if ($your_points == 1) {
		$prob_if_win = 1;
	    } else {
		$prob_if_win = $points[$your_points - 1][$opp_points];
	    }
	    if ($opp_points == 1) {
		$prob_if_lose = 0;
	    } else {
		$prob_if_lose = $points[$your_points][$opp_points - 1];
	    }

	    $points[$your_points][$opp_points] =
		     $prob_win  * $prob_if_win +
		(1 - $prob_win) * $prob_if_lose;
	}
    }

    return $points[$your_points_to_win][$opp_points_to_win];
}

sub volleyball_scoring ( $$$$ ) {
    my ($your_poins_to_win,
	$opp_points_to_win,
	$prob_win_when_serving,
	$prob_win_when_receiving) = @_;

    if ($your_points_to_win <= 0) {
	return 1;
    }

    if ($opp_points_to_win <= 0) {
	return 0;
    }

    my @points;
    for (my $your_points = 1; $your_points <= $your_points_to_win; $your_points++) {
	for (my $opp_points = 1; $opp_points <= $opp_points_to_win; $opp_points++) {
	    my ($prob_if_win_point, $prob_if_lose_point);
	    if ($your_points == 1) {
		$prob_if_win_point = 1;
	    } else {
		$prob_if_win_point = $points[$your_points - 1][$opp_points][1];
	    }
	    if ($opp_points == 1) {
		$prob_if_lose_point = 0;
	    } else {
		$prob_if_lose_point = $points[$your_points][$opp_points - 1][0];
	    }

	    # solving the two equations below...
	    $points[$your_points][$opp_points][1] =
		((1 - $prob_win_when_serving) * (1 - $prob_win_when_receiving) * $prob_if_lose_point +
		 $prob_win_when_serving * $prob_if_win_point) /
		     (1 - $prob_win_when_receiving + $prob_win_when_receiving * $prob_win_when_serving);

	    # $points[$your_points][$opp_points][1] =
	    # 	     $prob_win_when_serving  * $points[$your_points][$opp_points][0] +
	    # 	(1 - $prob_win_when_serving) * $prob_if_win_point;

	    $points[$your_points][$opp_points][0] =
		     $prob_win_when_receiving  * $points[$your_points][$opp_points][1] +
		(1 - $prob_win_when_receiving) * $prob_if_lose_point;

	}
    }

    # 50% chance of starting with the serve
    return ($points[$your_points_to_win][$opp_points_to_win][1] +
	    $points[$your_points_to_win][$opp_points_to_win][0]) / 2;
}

# ----------------------

my $tb = new Text::Table;
$tb->add("Tennis scoring: ",
         tennis_scoring($your_points_to_win, $opp_points_to_win, $prob_win_when_serving));
$tb->add("Volleyball scoring: ",
         volleyball_scoring($your_points_to_win, $opp_points_to_win, $prob_win_when_serving, $prob_win_when_receiving));
print $tb;

# ----------------------

__END__

=head1 AUTHOR

 Conan Yuan

=cut

