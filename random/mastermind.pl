#!/usr/local/bin/perl -w
# debuglvl	description
# 1		game level stuff
# 2		better guess level stuff
# 3		more better guess level stuff.
# 4		more better guess level stuff.
# 5		more better guess level stuff.
# 6		more better guess level stuff.
# 7		next guess level stuff
# 10		eval_guess level stuff

use strict;
use Getopt::Std;
use vars qw($opt_a $opt_d $opt_n $opt_m $opt_t $opt_w);
use IO::Handle;
autoflush STDERR 1;
autoflush STDOUT 1;
use Memoize;
memoize('better_guess');

getopts("a:d:n:m:t:w:") ||
  die "usage: fep $0 [-m(ax dig)] [-t(ries)] [-w(idth)] [-a(uto) <type>]";

# some default values
my $WIDTH   = (defined($opt_w) && $opt_w > 0) ? $opt_w : 4;
my $MAX_DIG = (defined($opt_m) && $opt_m > 0 && $opt_m < 10) ? $opt_m : 6;
my $TRIES   = (defined($opt_t) && $opt_t > 0) ? $opt_t : 8;
my $DEBUG = defined($opt_d) ? $opt_d : 0;
my $NUM = defined($opt_n) ? $opt_n : undef;
my $AUTO = $opt_a;

sub debug ( $$ ) {
    my ($debuglvl,$msg) = @_;
    print $msg if ($DEBUG > $debuglvl);
}

sub eval_guess ( $$$ ) {
    my ($width, $value, $guess) = @_;
    my (@used_in_guess, @used_in_value);
    my $exact = 0;
    my $close = 0;
    my $padding = "";
    map { $padding .= 0 } (1..$width);
    $guess .= $padding if (length($guess) < $width);
    # count exacts
    # digits are the same and in the same place
    for (my $ii = 0; $ii < $width; $ii++) {
	if (substr($value,$ii,1) eq substr($guess,$ii,1)) {
	    debug(10,"Matching char $ii exact\n");
	    $exact++;
	    $used_in_guess[$ii] = 1;
	    $used_in_value[$ii] = 1;
	}
    }
    # count closes
    # digits are the same, but in the wrong place
  GUESS_DIG:
    for (my $ii = 0; $ii < $width; $ii++) {
	next GUESS_DIG if ($used_in_guess[$ii]);
      VALUE_DIG:
	for (my $jj = 0; $jj < $width; $jj++) {
	    next VALUE_DIG if ($used_in_value[$jj]);
	    if (substr($guess,$ii,1) eq substr($value,$jj,1)) {
		debug(10,"Matching char $ii in guess close to $jj in value\n");
		$used_in_guess[$ii] = 1;
		$used_in_value[$jj] = 1;
		$close++;
		last VALUE_DIG;
	    }
	}
    }
    return ($exact, $close);
}

sub get_guess ( $$$$$@ ) {
    my ($width, $max_dig, $guesses_remaining, $auto, $seen_an_unordered_guess, @history) = @_;
    my $guess = 0;
    my $was_unordered_guess;
    if (defined($auto) && $auto eq "next") {
      NEXT:
	# we can optimize the next_guess if all the guesses have been automatic
	# this optimization only works because we know that
	# our guesses are going in order, which is only the case
	# if the guesses have all been automatic
	# or if the manual guess matches what we would have automatically chosen,
	# but we don't catch that case
	if (!$seen_an_unordered_guess && scalar(@history) > 0) {
	    $guess = next_guess($width, $max_dig, $history[$#history][0], @history);
	} else {
	    $guess = next_guess($width, $max_dig, undef, @history);
	}
	$was_unordered_guess = 0;
	print "Automatically guessing $guess\n";
    }
    elsif (defined($auto) && $auto eq "better") {
      BETTER:
	$guess = better_guess($width, $max_dig, @history);
	$was_unordered_guess = 1;
	print "Automatically guessing $guess\n";
    }
    else {
	do {
	    if ($guess !~ /^\d+$/) {
		if ($guess =~ /auto/i) {
		    goto BETTER;
		}
		elsif ($guess =~ /next/i) {
		    goto NEXT;
		}
		elsif ($guess =~ /better/i) {
		    goto BETTER;
		}
		print "Invalid guess, try again.\n";
	    }
	    print "You have $guesses_remaining guess"
	      . ($guesses_remaining > 1 ? "es" : "")
		. " remaining.\n";
	    print "Please enter a guess: ";
	    $guess = <STDIN>;
	    if (!defined($guess)) {
		# eof
		print "\nQuitting...Thanks for playing mastermind\n";
		exit(0);
	    } else {
		chomp($guess);
	    }
	} until ($guess =~ /^\d+$/);
	$was_unordered_guess = 1;
    }
    return ($guess, $was_unordered_guess);
}

sub mastermind ( $$$$$ ) {
    my ($width, $max_dig, $tries, $auto, $val) = @_;
    my @history = ();
    my $seen_an_unordered_guess = 0;
    if (!defined($val) || $val eq "") {
	map { $val .= int(rand($max_dig)) + 1 }  (1..$width);
    }
    print "A value has been selected.\n";
    print "It is $width digit" . ($width > 1 ? "s" : "") . " long.\n";
    print "Each digit is between 1 and $max_dig inclusive.\n";
    for (my $ii = $tries; $ii > 0; $ii--) {
	debug(1,"the number is $val\n");
	my ($guess, $was_unordered) = get_guess($width, $max_dig, $ii, $auto, $seen_an_unordered_guess, @history);
	$seen_an_unordered_guess ||= $was_unordered;
	debug(1,"got guess: $guess\n");
	my ($exact, $close) = eval_guess($width, $val, $guess);
	push @history, [ $guess, $exact, $close ];
	debug(1,"$exact exact, $close close\n");
	if ($exact == $width) {
	    print "You got it: $val\n";
	    # return number of tries needed;
	    return $tries - $ii + 1;
	} else {
	    print "Not quite.\n";
	    print "$exact digits were correct and in the correct place.\n";
	    print "$close digits were correct and in the incorrect place.\n";
            my $pv = get_possible_values($width, $max_dig, @history);
	    print scalar(@$pv) . " possibilities remaining.\n";
	}
    }
    print "Sorry, no more tries.  The answer was $val\n";
    return -1;
}

###
### an automatic solver
###
### brute force algorithm
### not exactly an efficient implementation either
###
sub increment ( $$$ ) {
    my ($width, $max_dig, $value) = @_;
    my (@digs) = split '', $value;
    my $cur_dig = $#digs;
    # ripple
    while($cur_dig >= 0 && ++$digs[$cur_dig] > $max_dig) {
	$digs[$cur_dig] = 1;
	$cur_dig--;
    }
    return join("", @digs);
}

sub next_guess ( $$$@ ) {
    my ($width, $max_dig, $last_ordered_val, @history) = @_;
    my $min_val = "";
    map { $min_val .= 1 } (1..$width);
    my $max_val = "";
    map { $max_val .= $max_dig } (1..$width);
    my $guess = $min_val;
    if (defined($last_ordered_val)) {
	if ($last_ordered_val == $max_val) {
	    return -1;
	}
	$guess = increment($width,$max_dig,$last_ordered_val);
    }
    do {
	foreach my $trial (@history) {
	    my ($try, $try_exact, $try_close) = @$trial;
	    debug(7,"$guess vs $try\n");
	    my ($guess_exact, $guess_close) = eval_guess($width, $guess, $try);
	    if ($guess_exact != $try_exact ||
		$guess_close != $try_close) {
		goto GUESS;
	    }
	}
	return $guess;
      GUESS:
	$guess = increment($width, $max_dig, $guess);
    } while ($guess != $min_val);
    # Can't find a valid guess
    # return a negative value for use with better_guess
    # otherwise, would probably return a harmless value like $guess or $min_val
    return -1;
}

#
# Define a value V and a guess G, both numbers with width digits.
# The result is the number of digits
# that V and G have in common in the same place and the number of digits
# in common in the wrong place (the output of eval_guess).
#
# The problem is to find V with the fewest number of guesses, where after
# each guess, you are given a result.
#
# After X guesses and X results, there is a set S of possible values.
# This is also the set of possible guesses since each value is equally likely.
#
# After our next guess and result, there will be a set S' of possible values.
#
# Suppose we guess G.  Then we can look at all the possible values in S and
# determine the possible results that we get.  Each value will give one result.
# Many of the values would give the same result.  For each result, there is a set
# S' of possible values.
#
# This next algorithm attempts to minimize the expected size of S'.
# So foreach G in S, we can find the expected size of S'
#    (by taking the expectation over all possibilities in S)
# Then we can choose the G which results in the smallest |S'|
#
# If a smaller set of possibilities is directly correlated to fewer guesses
# required, this is an optimal strategy.
#
# This is not necessarily an efficient implementation of that strategy.
#
sub get_possible_values ( $$@ ) {
    my ($width, $max_dig, @history) = @_;
    my (@possible_values) = ();
    for (my $guess = next_guess($width, $max_dig, undef, @history);
	 $guess > 0;
	 $guess = next_guess($width, $max_dig, $guess, @history)) {
	debug(3,"$guess\r");
	push (@possible_values, $guess);
    }
    debug(2,scalar(@possible_values) . " possible guesses.\n");
    return \@possible_values;
}

sub get_equivalence_class ( $$ ) {
    my ($guess, $digs_seen) = @_;
    my $equivalence_class = "";
    my %temp_dig_map;
    my $next_temp_dig = "A";
    foreach my $dig (split '', $guess) {
	if (defined($digs_seen->{$dig})) {
	    $equivalence_class .= $dig;
	}
	elsif (defined($temp_dig_map{$dig})) {
	    $equivalence_class .= $temp_dig_map{$dig};
	}
	else {
	    $equivalence_class .= $next_temp_dig;
	    $temp_dig_map{$dig} = $next_temp_dig;
	    # magical auto-increment of strings in perl
	    # works (with carry, preserving case) as long as the string
	    # is only used in string contexts since its creation
	    $next_temp_dig++;
	}
    }
    debug(6, "equivalence_class of $guess --> \"$equivalence_class\"\n");
    return $equivalence_class;
}

sub better_guess ( $$@ ) {
    my ($width, $max_dig, @history) = @_;
    my $possible_values_ref = get_possible_values($width, $max_dig, @history);
    my @possible_values = @$possible_values_ref;
    my %digs_seen = ();
    my $unseen_digs_equivalent = 0;
    if (scalar(@possible_values) > 10) {
	$unseen_digs_equivalent = 1;
	foreach my $trial (@history) {
	    my ($try, $try_exact, $try_close) = @$trial;
	    foreach my $dig (split '', $try) {
		$digs_seen{$dig} = 1;
	    }
	}
    }
    my $best_guess;
    my $min_expected_number_of_values_per_result;
    my %equivalent_guess_seen;
    foreach my $guess (@possible_values) {
	# optimize based on the fact that digits that haven't
	# appeared in any guess so far are equivalent
	if ($unseen_digs_equivalent) {
	    my $equivalence_class = get_equivalence_class($guess, \%digs_seen);
	    if (defined($equivalent_guess_seen{$equivalence_class}) && $equivalent_guess_seen{$equivalence_class}) {
		next;
	    }
	    $equivalent_guess_seen{$equivalence_class} = 1;
	}
	# if you guess $guess
	# %all_possible_results holds the number of values which
	# would give each result (a result being an exact/close pair)
	my %all_possible_results = ();
	foreach my $value (@possible_values) {
	    if ($value ne $guess) {
		my ($guess_exact, $guess_close) = eval_guess($width, $value, $guess);
		push(@{$all_possible_results{$guess_exact}{$guess_close}}, $guess);
	    }
	    #
	    # There is a possibility that we don't have to count, the one where
	    # the guess is correct, because every guess has the same chance
	    # of being correct.
	    #else {
	    #	@{$all_possible_results{$guess_exact}{$guess_close}} = ();
	    #}
	}
	#my $num_possible_values = 0;
	#
	# This implementation is less efficient but possibly easier to understand
	#
	#foreach my $num_exact (keys %all_possible_results) {
	#    foreach my $num_close (keys %{$all_possible_results{$num_exact}}) {
	#	$num_possible_values++;
	#    }
	#}
	#foreach my $num_exact (keys %all_possible_results) {
	#    foreach my $num_close (keys %{$all_possible_results{$num_exact}}) {
	#	# size of |S'| = num_values_for_this_result
	#	my $num_values_for_this_result =
	#	  scalar(@{$all_possible_results{$num_exact}{$num_close}});
	#	my $probability_of_this_result =
	#	  $num_values_for_this_result / $num_possible_values;
	#	$expectation{$guess} += $num_values_for_this_result * $probability_of_this_result;
	#    }
	#}
	my $expectation = 0;
	foreach my $num_exact (keys %all_possible_results) {
	    foreach my $num_close (keys %{$all_possible_results{$num_exact}}) {
		# size of |S'| = num_values_for_this_result
		# probablility of getting this result is the num_values_for_this_result
		# divided by the total number of possible values.
		# but the total number of possible values is the same for each guess,
		# so we'll leave it out.
		my $num_values_for_this_result =
		  scalar(@{$all_possible_results{$num_exact}{$num_close}});
		$expectation += $num_values_for_this_result * $num_values_for_this_result;
	    }
	}
	if (!defined($min_expected_number_of_values_per_result)
	    || $expectation < $min_expected_number_of_values_per_result) {
	    $best_guess = $guess;
	    $min_expected_number_of_values_per_result = $expectation;
	    debug(5,"new best guess: $guess, $expectation\n");
	}
	debug(3, sprintf("%8d %8d %8d %8d\r", $guess, $expectation,
			 $best_guess, $min_expected_number_of_values_per_result));
    }
    debug(3, "\n");
    if (!defined($best_guess)) {
	die "Can't find any guesses!";
    }
    return $best_guess;
}

my $ngames       = 0;
my $wins         = 0;
my $total_tries  = 0;
my $max_tries    = 0;
my $max_try_num  = undef;
my $first_num    = $NUM;
while (1) {
    $ngames++;
    if (defined($AUTO)) {
	#print "Press enter to begin game $ngames.  ";
	#my $foo = <STDIN>;
    }
    my $tries = mastermind($WIDTH,$MAX_DIG,$TRIES,$AUTO,$NUM);
    if ($tries > 0) {
	$wins++;
	$total_tries += $tries;
    } else {
	$total_tries += $TRIES;
    }
    if ($tries > $max_tries) {
        $max_tries = $tries;
        $max_try_num = $NUM // "";
    }
    print("--------------------------------------------------------------\n");
    print("$wins wins out of $ngames games\n");
    printf("%.4g%% win rate\n", ($wins/$ngames*100));
    printf("%d tries at most ($max_try_num)\n", $max_tries);
    printf("%d guesses (%.2g tries per game)\n",
	   $total_tries, ($total_tries/$ngames));
    print("--------------------------------------------------------------\n");

    if (defined($NUM)) {
        $NUM = increment($WIDTH, $MAX_DIG, $NUM);
        if ($NUM == $first_num) {
            exit;
        }
    }
    exit;
}
