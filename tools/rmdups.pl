#!/usr/bin/env perl
#

=head1 SYNOPSIS

  rmdups.pl [-FS <separator>] [-exclude <string>] <string>*

=head1 DESCRIPTION

Given a list of strings, return the list with duplicates elements
removed.  The order of elements will be the order in which they first
appear in the original list.

To get the list of strings, takes its arguments, join the arguments
with space (" "), then split them again with $FS, which defaults to
space, but can be specified with the -F or -FS options.

If there are no arguments, read from stdin and assume that each line
is a list.  Split the line by FS to get the list.

If you pass in elements to exclude with -exclude, this will filter out
those elements.

Can be useful for fixing up a PATH

=cut

use strict;
use Getopt::Long;

my $FS = " ";
GetOptions("FS|F=s" => \$FS,
           "exclude|e=s" => \my @EXCLUDE,
          )
    or die();

sub contains($$) {
    my ($elt, $list) = @_;
    return scalar(grep {$elt eq $_} @$list) > 0;
}

sub rmdups($) {
    my ($list) = @_;
    my @new;
    for my $elt (@$list) {
        push(@new, $elt) if (!contains($elt, \@new));
    }
    return @new;
}

sub filter {
    return grep {!contains($_, \@EXCLUDE)} @_;
}

sub fix($) {
    my ($str) = @_;
    my @list = split(/$FS/, $str);
    my @new = filter(rmdups(\@list));
    return wantarray ? @new : join($FS, @new);
}

if (@ARGV > 0) {
    print fix(join(' ', @ARGV)) . "\n";
} else {
    while (my $line = <>) {
        chomp($line);
        print fix($line) . "\n";
    }
}

