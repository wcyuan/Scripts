#!/usr/local/bin/perl -w
#
# coin.pl
# @desc:  study the coin game
#
# Conan Yuan, 20060330
#

=head1 NAME

coin.pl - study the coin game

=head1 SYNOPSIS

  coin.pl [options] <strings>*

  Options: 
    --alpha_sz        alphabet size
    --string_len      default string length
    --fast            use short cuts rather than real brute force
    --help, -?        shows brief help message
    --perldoc         shows full documentation

  See also Getopt::Long for complete standard options list.

=head1 ARGUMENTS

=over

=item I<strings>

The strings to try.

 If no strings are provided, find the best string for a given alphabet size and string length.
 If one string is provided, find the best string to counter that string.  Use log_level INFO for details.  
 If more than one string is provided, find the probability the first string beats the other strings.  Use -verbose for more details.  

=back

=head1 OPTIONS

=over 4

=item I<--alpha_sz>

Size of the alphabet.  If we are talking about coin flipping, then the
alphabet only has size 2, Heads or Tails.  But this script uses 1 and
2 instead of H and T, so that the alphabet can have arbitrary size.

=item I<--string_len>

The length of a string.  If at least one string is provided, we just
use the length of the first string (all subsequent strings are
truncated to this length).  If no strings are provided, then we use
the option.  If no option is provided, default to 3.

In the standard game, where a winning string may be HHH or HHT, the
string length is 3 since you need to predict three coin flips in a row
to win.

=item I<--fast>

The script uses a few short cuts if you give it the chance with the
fast option.

1. It assumes that the best competitor against a particular string
ends with the first n-1 letters of the string.

2. It also assumes that the best average competitor is 1222... But
since the point of this script is to test that logic, if you don't
want to use logic to make it faster, you can use the brute option.

=item I<--help>

Print a brief help message and exit.

=item I<--perldoc>

Print the perldoc page and exit.

=back

=head1 DESCRIPTION

Study this question:

Coin triplets

Two players play the following game with a fair coin. Player 1 chooses
(and announces) a triplet (HHH, HHT, HTH, HTT, THH, THT, TTH, or TTT)
that might result from three successive tosses of the coin. Player 2
then chooses a different triplet. The players toss the coin until one
of the two named triplets appears. The triplets may appear in any
three consecutive tosses: (1st, 2nd, 3rd), (2nd, 3rd, 4th), and so
on. The winner is the player whose triplet appears first.

1. What is the optimal strategy for each player? With best play, who
is most likely to win?

2. Suppose the triplets were chosen in secret? What then would be the
optimal strategy?

3. What would be the optimal strategy against a randomly selected
triplet?

=head1 Examples

 $ coin 
 Len 3 and alpha sz 2
 The best "worst-case" string is 121, which is guaranteed to win with at least probability 0.333333333333333.
 The best competitor against that string is 112
 The best "average-case" string is 122, which will win with probability 0.579761904761905.

 $ coin -string_len 4
 Len 4 and alpha sz 2
 The best "worst-case" string is 1211, which is guaranteed to win with at least probability 0.357142857142857.
 The best competitor against that string is 2121
 The best "average-case" string is 2111, which will win with probability 0.557106782106782.

 $ coin -string_len 5
 Len 5 and alpha sz 2
 The best "worst-case" string is 21122, which is guaranteed to win with at least probability 0.346153846153846.
 The best competitor against that string is 12112
 The best "average-case" string is 12222, which will win with probability 0.536150553021583.

 $ coin -string_len 6
 Len 6 and alpha sz 2
 The best "worst-case" string is 122211, which is guaranteed to win with at least probability 0.34.
 The best competitor against that string is 212221
 The best "average-case" string is 211111, which will win with probability 0.521897136358131.

 $ coin -string_len 7
 Len 7 and alpha sz 2
 The best "worst-case" string is 1221211, which is guaranteed to win with at least probability 0.336734693877552.
 The best competitor against that string is 2122121
 The best "average-case" string is 2111111, which will win with probability 0.512811965756366.
 $ coin 121 111
 121 beats 111 with probability 0.6  (alpha sz 2)

 $ coin 121 
 112 beats 121 with probability 0.666666666666667  (alpha sz 2)
 121 wins against the average string with probability 0.48452380952381 (alpha sz 2)

=head1 TODO

Compare not only the probability of success, but how quickly the game ends (is that an interesting question?)

=cut

use strict;
use warnings 'all';
use Pod::Usage;
use Math::MatrixReal;
use Memoize;

use Getopt::Long;
use Log::Log4perl qw(:levels);

# ----------------------

Log::Log4perl->easy_init($ERROR);
my $logger = Log::Log4perl->get_logger();

# default values
my $alpha_sz = 2;
my $default_string_len = 3;

# parse command-line options
GetOptions( "alpha_sz=i" => \$alpha_sz,
	    "string_len=i" => \$default_string_len,
	    "fast!" => \my $fast,
            "verbose|v" => sub { $logger->level($DEBUG) },
	  )
    or pod2usage();

my $is_debug = $logger->is_debug();

# ----------------------

sub get_alpha ( $ ) {
    my ($size) = @_;
    return (1..$alpha_sz);
}

# generate all strings of a given length with a given alphabet
sub generate ( $$ ) {
    my ($len, $alpha_sz) = @_;
    my @alpha = get_alpha($alpha_sz);
    my @strings = ('');
    for (my $ii = 0; $ii < $len; $ii++) {
	@strings = map { my $str = $_; map { $str . $_ } @alpha } @strings;
    }
    return \@strings;
}
Memoize::memoize('generate');

sub compete ( $@ ) {
    my ($alpha_sz, @strings) = @_;

    # we can only calculate probability for one string at a time
    my $main_string = $strings[0];
    if (!defined($main_string)) {
	$logger->logconfess("No strings! alpha size $alpha_sz");
    }
    my $string_len = length $main_string;

    my @alpha = get_alpha($alpha_sz);
    my $alpha_str = join('', @alpha);

    # standardize lengths
    @strings = map {
	my $str = substr($_, 0, $string_len);
	if (length($str) != $string_len) {
	    $logger->logconfess("Invalid string $str.  len $string_len alpha size $alpha_sz, " . join(',', @strings));
	}
	if ($str !~ m/^[$alpha_str]*$/) {	
	    $logger->logconfess("Invalid string $str.  len $string_len alpha size $alpha_sz, " . join(',', @strings));
	}
	$str;
    } @strings;

    # remove duplicates
    my %losers = map { $_ => 1; } grep { $_ ne $main_string } @strings;

    # if we only have one string, then I guess it will win
    if (scalar(keys(%losers)) < 1) {
	return 1;
    }

    $logger->debug("String len $string_len, Alpha size $alpha_sz");
    $logger->debug("Calculating probability that $main_string wins against " . 
	  join(',', keys(%losers)));

    # What is the probability that a given player wins?  
    # First ask, what is the probability that a given player
    # wins given that we have seen X previous letters
    # Only the last string_len-1 letters matter.  

    # So take all possible strings of length len-1.  These
    # are our states.  From any given state, we either win
    # or we transition to another state.
    # for every state we have a transition rule, so we
    # have the same number of equations as unknowns, so we
    # can solve the system of linear equestions.  
    my $states = generate($string_len-1, $alpha_sz);
    my $nstates = scalar(@$states);
    my %state_to_num;
    for (my $ii = 0; $ii < scalar(@$states); $ii++) {
	$state_to_num{$states->[$ii]} = $ii;
	$logger->debug("$ii => $states->[$ii]");
    }

    # get transition rules
    # transition rules look like
    # P(hh) = 1/2 P(hhh) + 1/2 P(hht)
    # then we transform each rule so that all the Ps are on the
    # left and the constants are on the right.  
    # We also change P(xyz) to P(yz) unless xyz is a winning or losing condition.
    # If neither hhh nor hht are winning conditions, then this becomes
    # 1/2 P(hh) - 1/2 P(ht) = 0
    # If hhh is a winning condition, this becomes
    # P(hh) - 1/2 P(ht) = 1/2
    # If hht is a losing condition, this becomes
    # 1/2 P(hh) = 1/2
    my @rules;
    my @result = (0) x $nstates;
    my $trans_prob = 1 / $alpha_sz;
    for (my $ii = 0; $ii < scalar(@$states); $ii++) {
	my $state = $states->[$ii];
	my @rule = (0) x $nstates;
	# the left-hand side of the equation
	$rule[$ii] = 1;
	foreach my $next_step (@alpha) {
	    my $new_state = $state . $next_step;
	    if ($new_state eq $main_string) {
		# winning condition stays on the right 
		$result[$ii] = $trans_prob;
	    } elsif ($losers{$new_state}) {
		# losing condition is a nop, this term goes to zero
	    } else {
		# we neither won nor loss, so only the last len-1 letters matter
		$new_state = substr $new_state, 1;
		$rule[$state_to_num{$new_state}] -= $trans_prob;
	    }
	}
	push(@rules, \@rule);
    }

    # solve it!
    my $matrix = Math::MatrixReal->new_from_rows(\@rules);
    if ($is_debug) {
        print("Rules\n");
	print $matrix;
    }
    my $constants_mat = Math::MatrixReal->new_from_columns([\@result]);
    if ($is_debug) {
        print("Constants\n");
        print $constants_mat;
    }
    # We assume that the matrix is invertible -- technically when we
    # call inverse we should check to make sure the return value isn't
    # undef.
    my $solution = $matrix->inverse()->multiply($constants_mat); 
    if ($is_debug) {
        print("Solutions\n");
	print $solution;
    }
    my $prob = 0;
    my $state_prob = $trans_prob ** ($string_len-1);
    for (my $row = 1; $row <= scalar(@rules); $row++) {
        $prob += $solution->element($row, 1) * $state_prob;
    }
    return $prob;
}
Memoize::memoize('generate');

# for a given string, find the one string that beats it most effectively
sub best_competitor ( $$ ) {
    my ($string, $alpha_sz) = @_;

    my $possible_strings;
    if ($fast) {
	# the last n-1 letters of the best competitor will match the
	# first n-1 letters of the string in question this makes a lot
	# of sense, though I'm not sure how you prove it
	
	# there is probably also a way to figure out what the first letter
	# should be, but I'm not sure how (except in the three letter case)
	my $str = substr $string, 0, length($string)-1;
	my @possible_strings = map { $_ . $str } get_alpha($alpha_sz);
	$possible_strings = \@possible_strings;
    } else {
	# brute force:
	$possible_strings = generate(length $string, $alpha_sz);
    }

    my $best;
    my $best_prob;
    foreach my $competitor (@$possible_strings) {
	if ($competitor eq $string) {
	    next;
	}
	my $prob = compete($alpha_sz, $competitor, $string);
	if (!defined($best) || !defined($best_prob) || $prob > $best_prob) {
	    $best = $competitor;
	    $best_prob = $prob;
	}
    }
    return ($best, $best_prob);
}

# for a given string, how does it fare against the average competitor?
sub ave_competitor ( $$ ) {
    my ($string, $alpha_sz) = @_;
    my $possible_strings = generate(length $string, $alpha_sz);
    my $ave_prob;
    my $n_competitors;
    foreach my $competitor (@$possible_strings) {
	if ($competitor eq $string) {
	    next;
	}
	my $prob = compete($alpha_sz, $string, $competitor);
	$logger->info("$string vs $competitor - $prob");
	$ave_prob += $prob;
	$n_competitors++;
    }
    return ($n_competitors == 0 ? 0 : $ave_prob / $n_competitors);
}

# finds the string with the best "worst case" scenario
sub best_string ( $$ ) {
    my ($string_len, $alpha_sz) = @_;
    my $possible_strings = generate($string_len, $alpha_sz);
    my $best;
    my $best_prob;
    my $best_comp;
    foreach my $string (@$possible_strings) {
	my ($comp, $prob) = best_competitor($string, $alpha_sz);
	if (!defined($best) || !defined($best_prob) || !defined($best_comp) 
	    || $prob < $best_prob) {
	    $best = $string;
	    $best_comp = $comp;
	    $best_prob = $prob;
	}
    }
    return ($best, 1-$best_prob, $best_comp);
}

# finds the string with the best "average case" scenario
sub best_ave_string ( $$ ) {
    my ($string_len, $alpha_sz) = @_;
    my $possible_strings;
    if ($fast) {
	# the best average competitor is 1222...
	# because in general in most competitions between
	# two strings, either could win with equal likelihood,
	# so in the average, the few cases that are really dominant
	# have a big effect.  The most dominant pairing is 1222... against 2222....
	my @alpha = get_alpha($alpha_sz);
	$possible_strings = [ $alpha[0] . ($alpha[1] x ($string_len - 1)) ];
    } else {
	$possible_strings = generate($string_len, $alpha_sz);
    }
    my $best;
    my $best_prob;
    foreach my $string (@$possible_strings) {
	my $prob = ave_competitor($string, $alpha_sz);
	if (!defined($best) || !defined($best_prob)
	    || $prob > $best_prob) {
	    $best = $string;
	    $best_prob = $prob;
	}
    }
    return ($best, $best_prob);
}


# ----------------------
# main

my @strings = @ARGV;
if (scalar(@strings) == 0) {
    my ($best, $prob, $comp) = best_string($default_string_len, $alpha_sz);
    print "Len $default_string_len and alpha sz $alpha_sz\n";
    print "The best \"worst-case\" string is $best, which is guaranteed to win with at least probability $prob.\n";
    print "The best competitor against that string is $comp\n";

    my ($best_ave, $ave_prob) = best_ave_string($default_string_len, $alpha_sz);
    print "The best \"average-case\" string is $best_ave, which will win with probability $ave_prob.\n";
} elsif (scalar(@strings) == 1) {
    my ($best, $prob) = best_competitor($strings[0], $alpha_sz);
    print "$best beats $strings[0] with probability $prob  (alpha sz $alpha_sz)\n";
    my ($ave_prob) = ave_competitor($strings[0], $alpha_sz);
    print "$strings[0] wins against the average string with probability $ave_prob (alpha sz $alpha_sz)\n";
} else {
    my $prob = compete($alpha_sz, @strings);
    print "$strings[0] beats " . join(',', @strings[1..$#strings]) . " with probability $prob  (alpha sz $alpha_sz)\n";
}

# ----------------------

__END__

=head1 AUTHOR

 Conan Yuan

=cut

