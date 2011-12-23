#!/usr/local/bin/perl -w
#
# enumerate.pl
# @desc:  Enumerate ways to choose one element from N buckets where each bucket has different number of objects
#
# Conan Yuan, 20070209
#

=head1 NAME

enumerate.pl - Enumerate ways to choose one element from N buckets where each bucket has different number of objects

=head1 SYNOPSIS

  enumerate.pl [options] 

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

=item I<--help>

Print a brief help message and exit.

=item I<--perldoc>

Print the perldoc page and exit.

=back

=head1 DESCRIPTION

Suppose you have N buckets.  Each bucket has a different size.  Call a
Choice a set of one object from each bucket.  Enumerate all the
possible Choices.

=cut

use strict;
use warnings 'all';
use Pod::Usage;
use Getopt::Long;
use Log::Log4perl qw(:levels);
use Text::Table;

# ----------------------

Log::Log4perl->easy_init($ERROR);
my $logger = Log::Log4perl->get_logger();

# default values
my @BUCKETS = ( ["a", "b", "c", ],
		[1, 2, 3, 4, 5, 6, ],
		["Washington", "Adams", "Jefferson", "Madison", ],
		["Maine", "Massachusetts", "Pennsylvania", "New York", "Kentucky", ],
	      );
my $MAX_BUCKET_SIZE = 10;
my $N_BUCKETS = 4;

# parse command-line options
GetOptions("num_buckets=i" => \$N_BUCKETS,
	   "max_bucket_size|max=i" => \$MAX_BUCKET_SIZE,
	   "bucket_size|size|b=i" => \my @BUCKET_SIZES,
	   "random_bucket_sizes|random|rand|r!" => \my $RANDOM_BUCKET_SIZES,
	   "recursive|recur!" => \my $USE_RECURSIVE,
	   "grey_code|gray_code|greycode|graycode|grey|gray|g!" => \my $USE_GREYCODE,
            "verbose" => sub { $logger->level($DEBUG) },
            "log_level=s" => sub { $logger->level($_[1]) },
	  );

# parse script arguments
pod2usage("Wrong number of arguments") unless @ARGV == 0;

# ----------------------
# get buckets

if (scalar(@BUCKET_SIZES) <= 0 && $RANDOM_BUCKET_SIZES) {
    print "Randomizing bucket sizes for $N_BUCKETS buckets, max size $MAX_BUCKET_SIZE\n";
    map {
	push(@BUCKET_SIZES, int(rand($MAX_BUCKET_SIZE) + 1));
    } (1..$N_BUCKETS);
    print("Bucket sizes: " . join(', ', @BUCKET_SIZES) . "\n");
}

if (scalar(@BUCKET_SIZES) > 0) {
    @BUCKETS = ();
    foreach my $size (@BUCKET_SIZES) {
	push(@BUCKETS, [map {$_} (1..$size)]);
    }
} else {
    # use default buckets
}

# ----------------------

# recursive
sub enumerate_r ( @ );
sub enumerate_r ( @ ) {
    my @buckets = @_;
    my $n_buckets = scalar(@buckets);
    if ($n_buckets == 0) {
	return ([]);
    } elsif ($n_buckets == 1) {
	return (map {[$_]} @{$buckets[0]});
    }
    my $bucket = $buckets[0];
    # copy all the buckets?  inefficient!  oh well.  
    my @rest = @buckets[1..($n_buckets-1)];
    my @choices;
    map {
	my $val = $_;
	map {
	    push(@choices, [$val, @$_]);
	} enumerate_r(@rest);
    } @$bucket;
    return @choices;
}

# recursive greycode
sub enumerate_g_r ( @ );
sub enumerate_g_r ( @ ) {
    $logger->logconfess("Not Implemented");
}

# iterative
sub enumerate_i ( @ ) {
    my @buckets = @_;
    my @choices;
    my @which;
    while (1) {
	my @choice;
	for (my $ii = 0; $ii < scalar(@buckets); $ii++) {
	    # initialize which
	    if (!defined($which[$ii])) {
		$which[$ii] = 0;
	    }

	    # add to the choice
	    push(@choice, $buckets[$ii]->[$which[$ii]]);
	}

	# operate on the choice
	# could print it out, but in this case just accumulate
	push(@choices, \@choice);

	# increment which
	for (my $jj = scalar(@buckets) - 1; $jj >= 0; $jj--) {
	    # starting with the last bucket, take the next element
	    $which[$jj]++;
	    
	    # overflow, we've reached the end of this bucket, 
	    # go back to the first element, then ripple on
	    # to the next bucket
	    if ($which[$jj] >= scalar(@{$buckets[$jj]})) {
		# if there are no more buckets to ripple to,
		# then we are done.
		if ($jj == 0) {
		    return @choices;
		}
		$which[$jj] = 0;
	    } else {
		# we stopped overflowing, so we can stop rippling
		last;
	    }
	}
    }
}

# iterative greycode
sub enumerate_g_i ( @ ) {
    my @buckets = @_;
    my @choices;
    my @which;
    my @direction;
    while (1) {
	my @choice;
	for (my $ii = 0; $ii < scalar(@buckets); $ii++) {
	    # initialize which
	    if (!defined($which[$ii])) {
		$which[$ii] = 0;
	    }

	    # add to the choice
	    push(@choice, $buckets[$ii]->[$which[$ii]]);
	}

	# operate on the choice
	# could print it out, but in this case just accumulate
	push(@choices, \@choice);

	# increment which
	for (my $jj = scalar(@buckets) - 1; $jj >= 0; $jj--) {
	    # starting with the last bucket, take the next element
	    if (!defined($direction[$jj])) {
		$direction[$jj] = 1;
	    }

	    # overflow, we've reached the end of this bucket, 
	    # ripple on to the next bucket
	    if (($direction[$jj] > 0 && $which[$jj] >= $#{$buckets[$jj]}) ||
		($direction[$jj] < 0 && $which[$jj] <= 0))
	    {
		# if there are no more buckets to ripple to,
		# then we are done.
		if ($jj == 0) {
		    return @choices;
		}
		$direction[$jj] *= -1;
	    } else {
		# no overflow, so we can stop rippling
		$which[$jj] += $direction[$jj];
		last;
	    }
	}
    }
}

# print an array of arrays
sub print_choices ( @ ) {
    my $tb = new Text::Table();
    map { $tb->add(@{$_}) } @_;
    print $tb;
}

# ----------------------

my @choices;
if ($USE_RECURSIVE) {
    if ($USE_GREYCODE) {
	@choices = enumerate_g_r(@BUCKETS);
    } else {
	@choices = enumerate_r(@BUCKETS);
    }
} else {
    if ($USE_GREYCODE) {
	@choices = enumerate_g_i(@BUCKETS);
    } else {
	@choices = enumerate_i(@BUCKETS);
    }
}
print_choices(@choices);

# ----------------------

__END__

=head1 AUTHOR

 Conan Yuan
 $Revision: 1.4 $
 $Source: /u/yuanc/testbed/PL/random/RCS/enumerate.pl,v $

=cut

