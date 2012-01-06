#!perl -w
#
# How many letters remain in a game of Words With Friends?  
#

use strict;
use warnings 'all';

my %FREQ = ( A => 9,
	     B => 2,
	     C => 2,
	     D => 5,
	     E => 13,
	     F => 2,
	     G => 3,
	     H => 4,
	     I => 8,
	     J => 1,
	     K => 1,
	     L => 4,
	     M => 2,
	     N => 5,
	     O => 8,
	     P => 2,
	     Q => 1,
	     R => 6,
	     S => 5,
	     T => 7,
	     U => 4,
	     V => 2,
	     W => 2,
	     X => 1,
	     Y => 2,
	     Z => 1,
	     _ => 2,
	     );

my %used;
while (my $line = <>) {
    chomp($line);
    # ignore whitespace
    $line =~ s/\s//g;
    # convert to upper case
    $line = uc $line;
    # convert into an array of characters
    my @letters = split '', $line;
    foreach my $l (@letters) {
      $used{$l}++;
    }
}

my @remaining;
foreach my $letter (sort keys(%FREQ)) {
    $used{$letter} //= 0;
    my $remaining = $FREQ{$letter} - $used{$letter};
    printf('%s => %d (%d total - %d used)' . "\n", 
	   $letter, $remaining,
	   $FREQ{$letter}, $used{$letter},
	  );
    push(@remaining, ($letter) x $remaining);
}

print "\n" . scalar(@remaining) . " letters remain:\n";
print join(' ', @remaining) . "\n";
