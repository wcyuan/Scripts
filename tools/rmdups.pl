#!/usr/local/bin/perl -w
#
# Given a line, return the line with duplicates removed.
# Also, remove certain specified elements.
#
# Can be useful for fixing up a PATH
#
use strict;
use Getopt::Long;

my $FS = " ";
GetOptions("FS|F=s" => \$FS,
           "exclude|e=s" => \my @EXCLUDE,
          );

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

