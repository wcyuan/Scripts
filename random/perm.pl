#!/usr/local/bin/perl -w 
#############################################################
###
### print all permutations of a list
###
use strict;

my $do_iterative = 1;

sub permute ( @ );
sub permute ( @ ) {
    my @list = @_;
    my $len = scalar(@list);
    if ($len == 1) {
	return map { [$_] } @list;
    }
    my @retval;
    for (my $ii = 0; $ii < $len; $ii++) {
	map {
	    push(@retval, [$list[$ii], @$_]);
	} permute(@list[0..$ii-1], @list[$ii+1..$#list]);
    }
    return @retval;
}
if (!$do_iterative) {
    map {print join(" ", @$_) . "\n"} permute(@ARGV);
}


if ($do_iterative) {
    my @list = @ARGV;
    my $len  = scalar(@list);

    sub print_permutation($$) {
        my ($list, $permutation) = @_;
        print join(' ', map { $list->[$_] } @$permutation) . "\n";
    }

    sub initial_permutation($) {
        my ($len) = @_;
        return [0..($len-1)];
    }

    # This logic is the key to the iterative mode.  Here's the idea:
    #
    # We want to step through all permutations in order.  E. g.:
    # A B C D
    # A B D C
    # A C B D
    # A C D B
    # A D B C
    # A D C B
    # B A C D
    # B A D C
    # B C A D
    # B C D A
    # B D A C
    # B D C A
    # C A B D
    # C A D B
    # C B A D
    # C B D A
    # C D A B
    # C D B A
    # D A B C
    # D A C B
    # D B A C
    # D B C A
    # D C A B
    # D C B A
    #
    # In the each column, we go in the same order.  In the first
    # column, we start with A, then print all permutations of BCD that
    # go with A.  Then we go to B, and print all permutations of ACD
    # that go with B, etc.
    #
    # To put it another way, once you've figured out the first i
    # columns, you basically keep printing those as prefixes to a
    # complete permutation of the remaining n-i columns.  
    #
    # How do you increment a permutation to the next permutation?
    # Basically, the idea is that one of the columns should be ready
    # to be incremented to the next highest value.  For example,
    # consider the first permutation of a list of 4:
    #
    #  1 2 3 4
    #
    # To get to the next value, you want to increment something to the
    # next highest value.  Start from the right, with the 4.  The 4
    # can't get any higher because the 1, 2, and 3 have already been
    # printed.  So then, move to the left, to the 3.  At this point,
    # the 1 and 2 have already been printed, so we have left to print
    # the 3 and the 4.  4 is greater than 3, so you can increment that
    # third column.  Thus, print a 4 there, and print the rest of the
    # numbers (3) in order.
    #
    # 1 2 4 3
    #
    # Let's take a more complicated example.  
    #
    # 2 1 4 3
    # 
    # Start on the right, with the 3.  That can't be incremented.
    # Then go to the 4.  The remaining digits and 3 and 4, and 4 is
    # the highest of these, so that can't be incremented either.  So
    # move on to the 1.  The remaining digits are (1, 3, 4).  1 can be
    # incremented to 3.  That leaves (1, 4), so print those out in
    # order to get:
    #
    # 2 3 1 4 
    #
    # This next_permutation logic is n^2 (worst case).  Haven't
    # figured out the amortized time (when you go through a complete
    # cycle of permutations).
    sub next_permutation($) {
        my ($permutation) = @_;
        my $len = scalar(@$permutation);
        my @remaining;
        for (my $ii = $len-1; $ii >=0; $ii--) {
            my $val = $permutation->[$ii];
            # find the first value in remaining larger than $val we
            # could speed this up with a binary search, the
            # next_permutation would be n log n.  Not sure how that
            # would change the amortized time.
            for (my $jj = 0; $jj < scalar(@remaining); $jj++) {
                if ($remaining[$jj] > $val) {
                    $permutation->[$ii] = $remaining[$jj];
                    $remaining[$jj] = $val;
                    for (my $kk = 0; $ii+$kk+1 < $len; $kk++) {
                        $permutation->[$ii+$kk+1] = $remaining[$kk];
                    }
                    return $permutation;
                }
            }
            push(@remaining, $val);
        }
        return undef;
    }

    my $p = initial_permutation($len);
    print_permutation(\@list, $p);
    while ($p = next_permutation($p)) {
        print_permutation(\@list, $p);
    }
}

