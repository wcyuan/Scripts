#!/usr/local/bin/perl -w
#
# sudoku.pl
# @desc:  solve sodukus
#
# Conan Yuan, 20060304
#

=head1 NAME

sudoku.pl - solve sodukus

=head1 SYNOPSIS

  sudoku.pl [options]

  Options:
    --help, -?        shows brief help message
    --perldoc         shows full documentation

  See also Getopt::Long for complete standard options list.

=head1 ARGUMENTS

=over

None.

=back

=head1 OPTIONS

=over 4

=item I<--slow>

stop after each step and show the user what it did

=item I<--file>

get puzzles from the given file
try top2365.txt

=item I<--help>

Print a brief help message and exit.

=item I<--perldoc>

Print the perldoc page and exit.

=back

=head1 DESCRIPTION

use -slow -verbose to see every step, -a to make sure it's unique

use any non-digit to represent a blank.  spaces are removed, so use
that to format the string.

$ sudoku.pl -slow -verbose -i '534.2769. 72.9.6... .6954..72    6.32149.7 4927..1.6 ..7..9234   97.....2. 2...9.7.. 34..72..9'

$ sudoku.pl -a -slow -verbose -i '..3...652...3621796.....843 3..12.765...6..381.6..539245.6.1...8...4.65.7.9......6'

To solve 36cube, run:
  sudoku.pl -36cube -input '123456 ------ ------ ------ ------ ------'
The first row can be set to 123456 without loss of generality.  The
problem is to assign a color to each spot.  Suppose you come up with a
solution.  The first row has to have six different colors.  Whatever
they are, you can rename those colors 123456.  So it's safe to start
with 123456, and assume that if there is a solution, it can be found
with that as the first row.

Note, it's correct that there is no solution...
  http://en.wikipedia.org/wiki/Latin_square
  http://en.wikipedia.org/wiki/Graeco-Latin_square
  http://en.wikipedia.org/wiki/36_cube
  http://en.wikipedia.org/wiki/Thirty-six_officers_problem

=cut

use strict;
use warnings 'all';
use Pod::Usage;
use Data::Dumper;
use Memoize qw(memoize);

use Getopt::Long;
#use Log::Log4perl qw(:levels);
use Time::HiRes;

# ----------------------

package Logger;

#
# Use this simple Logger class instead of Log::Log4perl because
# Log::Log4perl doesn't seem to be installed by default on cygwin.
#

use Carp;
use Data::Dumper;

our %LEVELS = (DEBUG      => 50,
               INFO       => 40,
               WARN       => 30,
               ERROR      => 20,
               LOGCONFESS => 10);
our %REVLEVELS = map { $LEVELS{$_} => $_ } keys(%LEVELS);

sub new($;$) {
    my ($this, $level) = @_;
    my $class = ref($this) || $this;
    my $self = {};
    $level //= 'WARN';
    $self->{level} = $level;
    bless $self, $class;
    return $self;
}

sub level($;$) {
    my ($self, $level) = @_;
    if (defined($level)) {
        if (defined($LEVELS{$level})) {
            $self->{level} = $level;
        } elsif (defined($REVLEVELS{$level})) {
            $self->{level} = $REVLEVELS{$level};
        } else {
            confess("Unknown level: $level");
        }
    }
    return $self->{level};
}

sub output($$$) {
    my ($self, $level, $msg) = @_;
    if ($LEVELS{$self->{level}} >= $LEVELS{$level}) {
        my ($pack, $fn, $line, $sub) = caller(2);
        my $str = "[$level][$sub:$line] $msg";
        if ($level eq 'LOGCONFESS') {
            confess($str);
        } else {
            print STDERR "$str\n";
        }
    }
}

sub debug($$)      { $_[0]->output('DEBUG',      $_[1]) }
sub info($$)       { $_[0]->output('INFO',       $_[1]) }
sub warn($$)       { $_[0]->output('WARN',       $_[1]) }
sub error($$)      { $_[0]->output('ERROR',      $_[1]) }
sub logconfess($$) { $_[0]->output('LOGCONFESS', $_[1]) }

# ----------------------

package main;

#Log::Log4perl->easy_init($ERROR);
#my $logger = Log::Log4perl->get_logger();
my $logger = new Logger();

# default values

# parse command-line options
GetOptions( "slow|s!"             => \my $slow,
	    "file|f=s"            => \my $infile,
	    "input|i=s"           => \my $input,
	    "max_dig_v|v=i"       => \my $MAX_DIGIT_V,
	    "max_dig_h|h=i"       => \my $MAX_DIGIT_H,
	    "num_to_do|n=i"       => \my $num_to_do,
	    "check_uniqueness|a!" => \my $check_uniqueness,
	    "generate|g!"         => \my $generate,
            "verbose"             => sub { $logger->level("DEBUG") },
            "log_level=s"         => sub { $logger->level($_[1]) },
            "36cube!"             => \my $tscube,
	  )
    or pod2usage();

$MAX_DIGIT_V //= $tscube ? 6 : 3;
$MAX_DIGIT_H //= $tscube ? 6 : 3;

my $MAX_DIGIT = ($MAX_DIGIT_V * $MAX_DIGIT_H);
if ($tscube) {
    $MAX_DIGIT = $MAX_DIGIT_V;
}

if (defined($infile) && $slow && $infile eq "-") {
    $logger->logconfess("slow mode doesn't work when the input file is stdin");
}

# parse script arguments
pod2usage("Wrong number of arguments") unless @ARGV == 0;

# ----------------------
# utility functions for the board representation

#
# elements
#

# zero indexed
sub elt ( $$ ) {
    my ($row, $col) = @_;
    return $row * $MAX_DIGIT + $col;
}
sub row ( $ ) {
    my ($elt) = @_;
    return int($elt / $MAX_DIGIT);
}
sub col ( $ ) {
    my ($elt) = @_;
    return ($elt % $MAX_DIGIT);
}
sub valid_elt ( $ ) {
    my ($val) = @_;
    return ($val =~ m/^\d+$/ && $val >= 0 && $val < $MAX_DIGIT*$MAX_DIGIT);
}
sub valid_rowcol ( $ ) {
    my ($val) = @_;
    return ($val =~ m/^\d+$/ && $val >= 0 && $val < $MAX_DIGIT);
}

sub valid_val ( $ ) {
    my ($val) = @_;
    return (defined($val) &&
	    $val =~ m/^\d+$/ &&
	    $val >= 1 &&
	    $val <= $MAX_DIGIT);
}

sub input_to_val ( $ ) {
    my ($input) = @_;
    if ($input =~ /[A-Z]/) {
	return 10 + ord($input) - ord('A');
    }
    if ($input =~ /[a-z]/) {
	return 10 + ord($input) - ord('a');
    }
    return $input;
}

sub val_to_output ( $ ) {
    my ($val) = @_;
    if ($val =~ /\d+/ && $val > 9) {
	return ("A".."Z")[$val-10];
    }
    return $val;
}

#
# groups
#
sub row_groups () {
    return map {
	my $start = ($_-1) * $MAX_DIGIT;
	my $end = $start+$MAX_DIGIT-1;
	[ $start..$end ];
    } (1..$MAX_DIGIT);
}
sub column_groups () {
    return map {
	my $index = $_ - 1;
	[ map {$_ * $MAX_DIGIT + $index} (0..$MAX_DIGIT-1) ];
    } (1..$MAX_DIGIT);
}
sub box_groups () {
    my @groups;
    for (my $ii = 0; $ii < $MAX_DIGIT_H; $ii++) {
	for (my $jj = 0; $jj < $MAX_DIGIT_V; $jj++) {
	    my @group;
	    my $first = $ii * ($MAX_DIGIT * $MAX_DIGIT_V) + $jj * $MAX_DIGIT_H;
	    for (my $kk = 0; $kk < $MAX_DIGIT_V; $kk++) {
		for (my $ll = 0; $ll < $MAX_DIGIT_H; $ll++) {
		    push(@group, $first + $kk * $MAX_DIGIT + $ll);
		}
	    }
	    push(@groups, \@group);
	}
    }
    return @groups;
    # equivalent to:
    #return map {
    #	my $first = $_;
    #	[ map { $first+$_ } (0, 1, 2, 9, 10, 11, 18, 19, 20)];
    #} (0, 3, 6, 27, 30, 33, 54, 57, 60);
}

sub tscube_groups() {
    my $grid = join('',
                    '6 5 2 3 1 4',
                    '2 4 1 6 3 5',
                    '3 1 4 2 5 6',
                    '5 6 3 4 2 1',
                    '4 2 5 1 6 3',
                    '1 3 6 5 4 2');
    $grid =~ s/\s*//g;
    my @groups;
    foreach (my $ii  = 0; $ii < length($grid); $ii++) {
        push(@{$groups[substr($grid, $ii, 1)-1]}, $ii);
    }

    # groups =
    #([4,  8, 13, 23, 27, 30],
    # [2,  6, 15, 22, 25, 35],
    # [3, 10, 12, 20, 29, 31],
    # [5,  7, 14, 21, 24, 34],
    # [1, 11, 16, 18, 26, 33],
    # [0,  9, 17, 19, 28, 32]);

    return @groups;
}

sub all_groups () {
    if ($tscube) {
        return (row_groups(), column_groups(), tscube_groups());
    } else {
        return (row_groups(), column_groups(), box_groups());
    }
}
memoize('all_groups');
{
    my @group_ids = all_groups();
    sub all_group_ids () {
	return (0..$#group_ids);
    }
    sub group_by_id ( $ ) {
	my ($id) = @_;
	$logger->logconfess("Internal error: no such group: $id")
	    unless(defined($group_ids[$id]));
	return $group_ids[$id];
    }
}
{
    my @elt_to_groups;
    my @elt_in_group;
    sub elt_group_ids ( $ ) {
	my ($elt) = @_;
	if (scalar(@elt_to_groups) == 0) {
	    foreach my $group_id (all_group_ids()) {
		my $group = group_by_id($group_id);
		foreach my $elt (@$group) {
		    push(@{$elt_to_groups[$elt]}, $group_id);
		    $elt_in_group[$group_id]{$elt} = 1;
		}
	    }
	    # sanity check
	    if (scalar(@elt_to_groups) != $MAX_DIGIT * $MAX_DIGIT) {
		$logger->logconfess("Error mapping element to group, not all elements are covered: " .
		      scalar(@elt_to_groups));
	    }
	    for (my $elt = 0; $elt < $MAX_DIGIT * $MAX_DIGIT; $elt++) {
		# hard code the sanity check that each element should
		# be in three groups
		if (scalar(@{$elt_to_groups[$elt]}) != 3) {
		    $logger->error("Error mapping element to group, element $elt in " .
                                   scalar(@{$elt_to_groups[$elt]}) . " groups");
		    print Dumper(map {group_by_id($_)} $elt_to_groups[$elt]) . "\n";
		    $logger->logconfess();
		}
	    }
	}
	return () unless valid_elt($elt);
	return @{$elt_to_groups[$elt]};
    }
    sub elt_groups ( $ ) {
	my ($id) = @_;
	map {group_by_id($_)} elt_group_ids($id);
    }
    memoize('elt_groups');
    sub elt_in_group ( $$ ) {
	my ($group, $elt) = @_;
	return $elt_in_group[$group]{$elt};
    }
    memoize('elt_in_group');
}

#
# boards
#

# 0 = no error
# 1 = values missing
# 2 = malformed group (duplicate values);
sub group_error ( $$ ) {
    my ($board, $group) = @_;
    my %filled;
    my @dup;
    my @missing;
    my %unfilled = map {$_ => 1} @$group;
    my $error = 0;
    foreach my $elt (@$group) {
	my $val = $board->[$elt];
	if (!valid_val($val)) {
	    return 1 unless wantarray;
	    next;
	}
	if (defined($filled{$val})) {
	    push(@dup, $val);
	    $error = 2;
	    return $error unless wantarray;
	} else {
	    push(@{$filled{$board->[$elt]}}, $elt);
	    delete($unfilled{$elt}) if (defined($unfilled{$elt}));
	}
    }
    for (my $ii = 1; $ii <= $MAX_DIGIT; $ii++) {
	if (!defined($filled{$ii})) {
	    push(@missing, $ii);
	    $error = 1 if (!$error);
	    return $error unless wantarray;
	}
    }
    return wantarray ? ($error, \@missing, [keys %unfilled], \@dup) : $error;
}
sub board_done ( $ ) {
    my ($board) = @_;
    foreach my $group (all_groups()) {
	if (group_error($board, $group)) {
	    return 0;
	}
    }
    return 1;
}
sub possible_vals ( $$ ) {
    my ($board, $elt) = @_;
    my %possible = map {$_ => 1} (1..$MAX_DIGIT);
    foreach my $group (elt_groups($elt)) {
	foreach my $group_elt (@$group) {
	    if (valid_val($board->[$group_elt]) && defined($possible{$board->[$group_elt]})) {
		delete $possible{$board->[$group_elt]};
	    }
	}
    }
    return keys %possible;
}

# ----------------------
# strategies
# modify the board in place.

sub trial_and_error ( $;$$$$ ) {
    my ($board, $poss_values, $depth, $elt, $n_solutions) = @_;
    $elt = 0 unless (defined($elt));
    $depth = 0 unless(defined($depth));
    if (!defined($n_solutions)) {
        if (!$check_uniqueness) {
            $n_solutions = 1;
        }
    }

    # Rather than just go through the elements in order
    # it would be better to do the one with the fewest
    # possible values first
    while ($elt < $MAX_DIGIT * $MAX_DIGIT && valid_val($board->[$elt])) {
	$elt++;
    }
    if ($elt > $MAX_DIGIT * $MAX_DIGIT) {
        my $is_solved = board_done($board);
        return wantarray ? ($is_solved, $board) : $is_solved;
    }
    my @poss;
    if (defined($poss_values)) {
	@poss = keys %{$poss_values->[$elt]};
    } else {
	@poss = possible_vals($board, $elt);
    }
    my @solutions;
    foreach my $val (@poss) {
	my @new_board = @$board;
	$new_board[$elt] = $val;
	my ($solved, $these_solutions) = standard(\@new_board, $depth);
	if ($solved) {
	    push(@solutions, @$these_solutions);
            if (defined($n_solutions) && scalar(@solutions) >= $n_solutions) {
                last;
            }
	}
    }
    if (scalar(@solutions) > 0) {
	@$board = @{$solutions[0][0]};
    }
    return wantarray ? (scalar(@solutions) > 0, \@solutions) : (scalar(@solutions) > 0);
}

# arr2 must be a subset of arr1 (string equality)
sub array_subset($$) {
    my ($arr1, $arr2) = @_;
    my %h1 = map {$_ => 1} @$arr1;
    foreach my $v (@$arr2) {
	return 0 if (!$h1{$v});
    }
    return 1;
}

sub array_equal($$) {
    my ($arr1, $arr2) = @_;
    return array_subset($arr1, $arr2) && array_subset($arr2, $arr1);
}

sub standard($;$) {
    my ($board, $depth) = @_;
    if (!defined($depth)) {
	$depth = 0;
    }
    my $changes = 1;
    my @possible_values;
 LOOP:
    while(!board_done($board) && $changes) {
	$changes = 0;
	#
	# RULE 1
	#
	# If there is only one possible value for a space
	# put that value in that space
	#
	for (my $elt = 0; $elt < $MAX_DIGIT * $MAX_DIGIT; $elt++) {
	    if (!valid_val($board->[$elt])) {
		my %allposs = map {$_ => 1} possible_vals($board, $elt);
		if (!defined($possible_values[$elt])) {
		    $possible_values[$elt] = \%allposs;
		} else {
		    foreach my $val (keys %{$possible_values[$elt]}) {
			if (!$allposs{$val}) {
			    $possible_values[$elt]{$val} = 0;
			    #undef $possible_values[$elt]{$val};
			}
		    }
		}
		my @poss = grep {$possible_values[$elt]{$_}} keys(%{$possible_values[$elt]});
		if (scalar(@poss) == 1) {
		    $board->[$elt] = $poss[0];
		    $changes = 1;
		    if ($slow && ($depth == 0)) {
			$logger->debug("Putting $poss[0] into $elt because that's the only possible value for that spot");
			$logger->debug("\n" . board_string($board));
			my $dummy = <>;
		    }
		} elsif (scalar(@poss) == 0) {
		    if ($slow || ($depth == 0)) {
			$board->[$elt] = "X";
			$logger->info("Impossible board, no values for $elt");
			$logger->info("\n" . board_string($board));
		    }
		    return 0;
		}
	    }
	}
	next if ($changes);

	#
	# RULE 2
	#
	# For each group, if there is only one place a given value
	# can go, put that value there
	#
	my @poss_elts_for_val;
	my %missing_group_values;
	my %unfilled_group_values;
	foreach my $group_id (all_group_ids()) {
	    my $group = group_by_id($group_id);
	    my ($error, $missing, $unfilled) = group_error($board, $group);
	    if ($error == 0) {
		next;
	    } elsif ($error == 2) {
		if ($depth == 0) {
		    $logger->logconfess("Malformed board:\n" . board_string($board));
		}
		if ($slow || ($depth == 0)) {
		    $logger->info("Impossible board: malformed");
		    $logger->info("\n" . board_string($board));
		    $logger->info(Dumper($group));
		}
		return 0;
	    } elsif ($error == 1) {
		$missing_group_values{$group_id} = $missing;
		$unfilled_group_values{$group_id} = $unfilled;
		# for each value that is missing from the group,
		# check all the empty spots in the group and see
		# for which spots have that value is a possible value.
		# if there is only one possble spot for a given value,
		# fill that spot in with that value
		foreach my $value (@$missing) {
		    my @poss = grep { $possible_values[$_]{$value}  } @$unfilled;
		    $poss_elts_for_val[$group_id]{$value} = \@poss;
		    if (scalar(@poss) == 0) {
			if ($slow || ($depth == 0)) {
			    $logger->info("Impossible board, no spots for $value");
			    $logger->info("\n" . board_string($board));
			    $logger->info(Dumper($group));
			    foreach my $elt (@$unfilled) {
				$board->[$elt] = "X";
				$logger->info("elt: $elt\n" . Dumper($possible_values[$elt]));
			    }
			}
			return 0;
		    } elsif (scalar(@poss) == 1) {
			my $elt = $poss[0];
			$board->[$elt] = $value;
			$changes = 1;
			if ($slow && ($depth == 0)) {
			    $logger->debug("Putting $value into $elt because that's the only possible spot for that value");
			    $logger->debug("\n" . board_string($board));
			    my $dummy = <>;
			}
			if ($slow) {
			    # This "next" can be removed.  It's only here because I want to see all
			    # RULE 1 changes before all RULE 2 changes
			    next LOOP;
			}
		    }
		}
	    } else {
		$logger->info("\n" . board_string($board));
		$logger->info(Dumper($group));
		$logger->logconfess("Bad output $error from group_error");
	    }
	}
	next if ($changes);

	#
	# RULE 3
	#
	# If in one group, all the possible occurrences of
	# a number appear in spots which are also part of
	# another group, then that number can't appear in
	# any other parts of the other group.
	#
	my @groups = keys %unfilled_group_values;
	#while (scalar(@groups) > 0) {
	    #my $group_id1 = shift(@groups);
	foreach my $group_id1 (@groups) {
	    foreach my $value (@{$missing_group_values{$group_id1}}) {
		my @spots = @{$poss_elts_for_val[$group_id1]{$value}};
		next unless(scalar(@spots) > 1);
		my %value_groups = map {$_ => 1} elt_group_ids($spots[0]);
		foreach my $elt (@spots) {
		    foreach my $group_id2 (keys %value_groups) {
			if (!$value_groups{$group_id2}) {
			    next;
			}
			if (!elt_in_group($group_id2, $elt)) {
			    $value_groups{$group_id2} = 0;
			    delete $value_groups{$group_id2};
			    next;
			}
			if (scalar(grep {$_ == $group_id2} @groups) == 0) {
			    $value_groups{$group_id2} = 0;
			    delete $value_groups{$group_id2};
			}
		    }
		}
		foreach my $group_id2 (keys %value_groups) {
		    if (!$value_groups{$group_id2}) {
			next;
		    }
		    my $spots2 = $poss_elts_for_val[$group_id2]{$value};
		    next if (!defined($spots2) || scalar(@$spots2) <= @spots);
		    foreach my $elt (@$spots2) {
			if (scalar(grep {$_ == $elt} @spots) == 0) {
			    $possible_values[$elt]{$value} = 0;
			    if ($slow && ($depth == 0)) {
				$logger->debug("$value can't go into $elt because it must go in " . join(",", @spots));
				my @copy = @$board;
				$copy[$elt] = "X";
				foreach my $s (@spots) {
				    $copy[$s] = "Y";
				}
				$logger->debug("\n" . board_string(\@copy));
				my $dummy = <>;
			    }
			    $changes = 1;
			    if ($slow) {
				# This "next" can be removed.  It's only here because I want to see all
				# RULE 1 changes before all RULE 3 changes
				next LOOP;
			    }
			}
		    }
		}
	    }
	}
	next if ($changes);

	if ($depth == 0) {
	    $logger->debug("Could not solve with 3 rules, relying on rules 4 and 5");
	    $logger->debug("\n" . board_string($board));
	}

	#
	# RULE 4
	#
	# If in a particular group, N of the missing values each must go in N possible places,
	# then nothing else can go in those places.
	# E.g. if the possible values for a row are:
	# 1-2 1-2 1-2-3 3-4-5 3-4-5
	# Then 4 and 5 must go in the last two places, and therefore
	# 3 cannot go in those places, so it must go in the third place.
	#
	# The program seems to be faster without this rule.
	#
	@groups = keys %unfilled_group_values;
	foreach my $group_id (@groups) {
	    my $group = group_by_id($group_id);
	    my @missing = @{$missing_group_values{$group_id}};
	    foreach my $value (@missing) {
		my @spots = @{$poss_elts_for_val[$group_id]{$value}};
		if (scalar(@spots) < 2) {
		    next;
		}
		if (scalar(@missing) < scalar(@spots)) {
		    next;
		}
		my @match_values = ();
		foreach my $val (@missing) {
		    my @spots2 = @{$poss_elts_for_val[$group_id]{$val}};
		    if (array_subset(\@spots, \@spots2)) {
			push(@match_values, $val);
		    }
		}
		if (scalar(@match_values) >= scalar(@spots)) {
		    my %matches = map { $_ => 1 } @match_values;
		    foreach my $elt (@spots) {
			foreach my $val (keys %{$possible_values[$elt]}) {
			    next if ($matches{$val});
			    next unless $possible_values[$elt]{$val};
			    $possible_values[$elt]{$val} = 0;
			    if ($slow && ($depth == 0)) {
				$logger->debug("$val can't go into $elt because these spots " . join(",", @spots) .
                                               " must contain these values " . join(',', @match_values));
				my @copy = @$board;
				foreach my $s (@spots) {
				    $copy[$s] = "X";
				}
				$logger->debug("\n" . board_string(\@copy));
				my $dummy = <>;
			    }
			    $changes = 1;
			    if ($slow) {
				# This "next" can be removed.  It's only here because I want to see all
				# RULE 1 changes before all RULE 3 changes
				next LOOP;
			    }
			}
		    }
		}
	    }
	}
	next if ($changes);

	#
	# RULE 5
	# If in a particular group, N of the unfilled spots must contain N possible values,
	# then none of those values can go in other spots.
	# 1-2 1-2 1-2-3 3-4-5 3-4-5
	# Then 1 and 2 must go in the first two places and therefore
	# cannot go in the third place.  Thus, the third place
	# must be a 3.
	#
	@groups = keys %unfilled_group_values;
	foreach my $group_id (@groups) {
	    my $group = group_by_id($group_id);
	    my @unfilled = @{$unfilled_group_values{$group_id}};
	    foreach my $spot (@unfilled) {
		my @vals = keys %{$possible_values[$spot]};
		if (scalar(@vals) < 2) {
		    next;
		}
		if (scalar(@unfilled) < scalar(@vals)) {
		    next;
		}
		my @match_spots = ();
		my %unmatch_spots;
		foreach my $spot2 (@unfilled) {
		    my @vals2 = keys %{$possible_values[$spot2]};
		    if (array_subset(\@vals, \@vals2)) {
			push(@match_spots, $spot2);
		    } else {
			$unmatch_spots{$spot2} = 1;
		    }
		}
		if (scalar(@match_spots) >= scalar(@vals)) {
		    foreach my $elt (keys %unmatch_spots) {
			foreach my $val (@vals) {
			    next unless $possible_values[$elt]{$val};
			    $possible_values[$elt]{$val} = 0;
			    if ($slow && ($depth == 0)) {
				$logger->debug("$val can't go into $elt because these vals " . join(",", @vals) .
                                               " must go in these spots " . join(',', @match_spots));
				my @copy = @$board;
				$copy[$elt] = "Y";
				foreach my $s (@match_spots) {
				    $copy[$s] = "X";
				}
				$logger->debug("\n" . board_string(\@copy));
				my $dummy = <>;
			    }
			    $changes = 1;
			    if ($slow) {
				# This "next" can be removed.  It's only here because I want to see all
				# RULE 1 changes before all RULE 3 changes
				next LOOP;
			    }
			}
		    }
		}
	    }
	}
	next if ($changes);
    }
    if (!board_done($board)) {
	if ($depth == 0) {
	    $logger->info("Could not fully solve, relying on trial and error");
	    $logger->info("\n" . board_string($board));
	    $logger->info("\n" . poss_vals_string(\@possible_values, $board));
	    if ($slow) {
		my $dummy = <>;
	    }
	}
	my ($solved, $solutions) = trial_and_error($board, \@possible_values, $depth+1);
        if ($solved > 0) {
            # Solved == 0 means it wasn't solved.  Solved == 1 means
            # it was solved with rules.  Solved == 2 means it was
            # solved with guessing.  If we got here, and it was
            # solved, it was solved with guessing.
            $solved++;
        }
	return wantarray ? ($solved, $solutions) : $solved;
    }
    return wantarray ? (1, [[$board, $depth]]) : 1;
}

# ----------------------
# reading and printing

sub read_board ( $ ) {
    my ($lines) = @_;
    my $board_string = "";
    if (ref($lines) ne "ARRAY") {
	$logger->error("Bad input into read_board, not an array ref: $lines");
    }
    while (scalar(@$lines) > 0 &&
	   (length($board_string) < $MAX_DIGIT * $MAX_DIGIT)) {
        $board_string .= shift(@$lines);
	$board_string =~ s/\s//g;
    }
    if (length($board_string) < $MAX_DIGIT * $MAX_DIGIT) {
	$logger->logconfess("Malformed board: $board_string");
    }
    $board_string = substr $board_string, 0, $MAX_DIGIT*$MAX_DIGIT;
    my @board = map {input_to_val($_)} split '', $board_string;
    return wantarray ? (\@board, $lines) : \@board;
}

sub board_string ( $;$ ) {
    my ($board, $format) = @_;
    if (ref($board) ne "ARRAY") {
	$logger->error("Malformed board, not an array: $board");
	return;
    }
    if (!defined($format)) {
	$format = 0;
    }
    my $ofs = "  ";
    my $ors = "\n";
    if ($format == 1) {
	$ofs = "";
	$ors = " ";
    }
    my $board_string;
    for (my $elt = 0; $elt < $MAX_DIGIT * $MAX_DIGIT; $elt++) {
	my $val = "-";
	if ($board->[$elt] eq "X" || $board->[$elt] eq "Y") {
	    $val = $board->[$elt];
	} elsif (valid_val($board->[$elt])) {
	    $val = $board->[$elt];
	}
	$board_string .= val_to_output($val);
	if (($elt+1) % ($MAX_DIGIT*$MAX_DIGIT_V) == 0) {
	    $board_string .= $ors . $ors;
	} elsif (($elt+1) % $MAX_DIGIT == 0) {
	    $board_string .= $ors;
	} elsif (($elt+1) % $MAX_DIGIT_H == 0) {
	    $board_string .= $ofs;
	}
    }
    return $board_string;
}

sub poss_vals_string ( $$ ) {
    my ($poss, $board) = @_;
    if (ref($board) ne "ARRAY" || ref($poss) ne "ARRAY") {
	$logger->error("Malformed board or possible values, not an array");
	return;
    }
    my $ofs = "\t";
    my $ors = "\n";
    my $board_string;
    for (my $elt = 0; $elt < $MAX_DIGIT * $MAX_DIGIT; $elt++) {
	my $val = "-";
	if ($board->[$elt] eq "X" || $board->[$elt] eq "Y") {
	    $val = $board->[$elt];
	} elsif (valid_val($board->[$elt])) {
	    $val = val_to_output($board->[$elt]);
	} else {
	    $val = join('', sort grep {$poss->[$elt]{$_}} keys(%{$poss->[$elt]}));
	}
	$board_string .= $val;
	if (($elt+1) % ($MAX_DIGIT*$MAX_DIGIT_V) == 0) {
	    $board_string .= $ors . $ors;
	} elsif (($elt+1) % $MAX_DIGIT == 0) {
	    $board_string .= $ors;
	} elsif (($elt+1) % $MAX_DIGIT_H == 0) {
	    $board_string .= $ofs . $ofs;
	} else {
	    $board_string .= $ofs;
	}
    }
    return $board_string;

}

# ----------------------

sub all_possibilities($) {
    my ($board) = @_;
    my @possible_vals;
    for (my $elt = 0; $elt < $MAX_DIGIT * $MAX_DIGIT; $elt++) {
        if (!valid_val($board->[$elt])) {
            $possible_vals[$elt] = [ possible_vals($board, $elt) ];
        }
    }
    return \@possible_vals;
}

sub add_random_value($;$) {
    my ($board, $possible_vals) = @_;

    my @missing_elts;
    for (my $elt = 0; $elt < $MAX_DIGIT * $MAX_DIGIT; $elt++) {
        if (!valid_val($board->[$elt])) {
            push(@missing_elts, $elt);
        }
    }

    my $n = int(rand(scalar(@missing_elts)));
    my $elt = $missing_elts[$n];
    my $poss;
    if (defined($possible_vals)) {
        $poss = $possible_vals->[$elt];
    } else {
        $poss = [ possible_vals($board, $elt) ];
    }
    my $p = int(rand(scalar(@$poss)));
    return ($elt, $poss->[$p]);
}

sub generate_board() {
    my $board = read_board([('-' x $MAX_DIGIT) x $MAX_DIGIT]);

    my ($result, $solutions, @last);
    my $poss = all_possibilities($board);
    while (1) {
        @last = @$board;
        my ($elt, $val) = add_random_value($board, $poss);
        $board->[$elt] = $val;

        ($result, $solutions) = trial_and_error([@$board], undef, 1, undef, 2);
        if ($result && scalar(@$solutions) > 1) {
            print board_string($board);
            print "Has at least " . scalar(@$solutions) . " solutions:\n";
            print join("---\n\n", map {board_string($_->[0])} @$solutions);
            print '=' x 20;
            print "\n";
            $poss = all_possibilities($board);
        } elsif ($result && scalar(@$solutions == 1)) {
            last;
        } elsif (!$result || scalar(@$solutions < 1)) {
            print board_string($board);
            print "Has no solutions, trying a different value\n";
            print '=' x 20;
            print "\n";
            $board = [ @last ];
            $poss->[$elt] = [ grep {$_ != $val} @{$poss->[$elt]} ];
        }
    }

    print board_string($board);
    print "Found " . scalar(@$solutions) . " solutions\n";
    print join("---\n\n", map {board_string($_->[0])} @$solutions);
    if (scalar(@$solutions == 0)) {
        print "Last consistent board:\n";
        print join('', @last) . "\n";
    } else {
        print join('', @$board) . "\n";
    }
}

# ----------------------
# main

# some examples
# can be solved with just rules 1 and 2.
my $easy = "-3------9 ----8723- 6-9-4-7-- -1--5-4-- --51-96-- --8-7--9- --4-2-3-8 -6381---- 8------1-";
# can be solved with just rules 1, 2, and 3.
my $hard = "--89-1--- 1-74--8-- -9-36---- 67------- --4---5-- -------26 ----37-8- --5--96-3 ---5-29--";
my $hard2 = "275-----6------7-5-4---7--3 --2968---------------1425-- 1--5---9-4-8------3-----461";
# needs more than 3 rules:
my $hard3 = "7-5-----2---4-1---3-------- -1-6--4--2---5-----------9- ---378----9----8---8-----6-";
# needs more than the rules coded
my $v_hard =  "-2-----7----5-8--4--------- 4---3---8-7--9--2-6---1---5 ---------5--6-4--1-3-----9-";
my $vv_hard = '-2-9--5----1-7-3---8-6--4-- --3-1--------------6-4---89 --7-5--------------9-3---24';
my $vvv_hard = '34-----16--63--7--8--6-5--- 5---3-29-----2-----28-9---5 ---8-1--7--9--36--68-----23';
# h = 4, v = 3
my $imbalanced = "--4--9C--6-- -A-7----8-9- ---2A--17---  ---39--71--- -B--1653--4- A9--------23  9C--------75 -7--C849--6- ---42--6B--- ---15--BC--- -4-8----9-1- --C--13--4--";

my $boards = [$easy, $hard, $hard2, $hard3, $v_hard, $vv_hard, $vvv_hard];
if ($MAX_DIGIT_H eq 4 && $MAX_DIGIT_V eq 3) {
    $boards = [$imbalanced];
}

if ($generate) {
    generate_board();
    exit;
}

if ($infile) {
    if ($infile eq "all" && !-f $infile) {
	$infile = "top2365.txt";
    }
    my $infd;
    open($infd, $infile)
	or $logger->logconfess("Can't open input $infile: $? $! $@");
    my @lines = <$infd>;
    close($infd)
	or $logger->logconfess("Can't close input $infile: $? $! $@");
    $boards = \@lines;
} elsif ($input) {
    $boards = [$input];
}
my @stats;
for (my $ii = 1;
     (!defined($num_to_do) || $ii <= $num_to_do) && scalar(@$boards) > 0;
     $ii++) {
    my $board = read_board($boards);
    print board_string($board);
    my $start = Time::HiRes::time();
    my ($result, $solutions) = standard($board);
    if ($result) {
	print "Solved ($result) $ii!\n";
	my $status;
	if ($result == 1) {
	    $status = "Solved using rules";
	} else {
	    if ($check_uniqueness) {
		my ($num_solutions) = scalar(@$solutions);
		$status = "Solved with guessing ($num_solutions solutions)";
		if ($num_solutions > 1) {
		    foreach my $sol (@$solutions) {
			my ($board, $depth) = @$sol;
			print "solution in depth $depth\n";
			print board_string($board);
		    }
		}
	    } else {
		my $depth = $solutions->[0][1];
		$status = "Solved with guessing ($depth depth)";
	    }
	}
	$stats[$ii]{status} = $status;
    } else {
	print "Unsolvable $ii!\n";
	$stats[$ii]{status} = "Unsolvable";
    }
    print board_string($board);
    my $end = Time::HiRes::time();
    $stats[$ii]{time} = $end - $start;
}

my $ii = 1;
foreach my $stat (@stats) {
    next unless defined($stat);
    print "Board $ii $stat->{status} in $stat->{time}\n";
    $ii++;
}

# ----------------------

__END__

=head1 AUTHOR

 Conan Yuan

=cut

