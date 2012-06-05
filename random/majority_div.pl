#!/usr/bin/perl
use strict;
if (my $result = &majority(<STDIN>)) {
	print $result;
}

sub majority {
	my $n = scalar(@_);
	if ($n == 1) {
		return $_[0];
	} elsif ($n == 2) {
		return(($_[0] eq $_[1]) ? $_[0] : undef);
	} else {
		my $thing1 = &majority(@_[0..int($n/2)]);
		my $thing2 = &majority(@_[int($n/2)+1..$n-1]);
		if (&count($thing1,@_) > $n/2) {
			return $thing1;
		} elsif (&count($thing2,@_) > $n/2) {
			return $thing2;
		} else {
			return undef;
		}
	}
}

sub count {
	my($element) = shift;
	return 0 unless defined($element);
	my $count = 0;
	foreach (@_) {
		$count++ if ($element eq $_);
	}
	return $count;
}
