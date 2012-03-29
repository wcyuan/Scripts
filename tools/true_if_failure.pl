#!/usr/local/bin/perl -w

use strict;

my $rc = system(@ARGV);
if ($rc == 0) {
    exit 1;
} else {
    exit 0;
}
