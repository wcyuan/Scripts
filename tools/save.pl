#!/usr/bin/env perl
#
# $Header$
#

=head1 NAME

  save - run a command, save output and command to a file

=head1 SYNOPSIS

  save <file> <cmd>

=head1 DESCRIPTION

Run a command and save both the output of the command and command
itself to a file

=cut

# -------------------------------------------------

use strict;
use warnings 'all';

use Carp;
use Getopt::Long;
use Pod::Usage;
use Sys::Hostname qw(hostname);

# -------------------------------------------------

Getopt::Long::Configure('pass_through');
GetOptions()
    or pod2usage("Invalid option");

unless (@ARGV > 1) {
    pod2usage("Not enough arguments");
}

my $file = shift(@ARGV);

# protect all the arguments in quotes except the first argument (which
# is presumably the command name.
my $cmd = join(' ', $ARGV[0], map {"'$_'"} @ARGV[1..$#ARGV]);

# -------------------------------------------------

if (-e $file) {
    carp("Overwriting file $file");
}

open(FD, '>', $file)
    or logconfess("Can't open $file: $? $! $@");

my $user = getpwuid($>) || getpwuid($<) || getlogin();
my $starttime = localtime();
my $host = hostname();

# Run in a separate bash shell so that it picks up aliases
my $output = `bash -i -c "$cmd 2>&1" 2>&1`;

my $endtime = localtime();

print FD "#\n";
print FD "# Wrapper    :  $0\n";
print FD "# Start Time :  $starttime\n";
print FD "# End Time   :  $endtime\n";
print FD "# User       :  $user\n";
print FD "# Host       :  $host\n";
print FD "# Command    :  $cmd\n";
print FD "#\n";
print FD "$output";
close(FD)
    or logconfess("Can't close $file: $? $! $@");

# -------------------------------------------------
