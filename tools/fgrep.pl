#!/usr/local/bin/perl -w
#
# fgrep.pl
# @desc:  like fgrep without the wordlist size restriction
#
# Conan Yuan, 20060517
#

=head1 NAME

fgrep.pl - like fgrep without the wordlist size restriction

=head1 SYNOPSIS

  fgrep.pl [options] [patternlist -- required if -f is not used]

  Options: 
    -v               reverse
    -i               case insensitive
    -f <patternlist> the pattern list, if you'd rather specify it this way
    -w               match words only
    -e               exact matching 
    --help, -?        shows brief help message
    --perldoc         shows full documentation

  See also Deshaw::Getopt::Long for complete standard options list.

=head1 ARGUMENTS

=over

=item I<patternlist>

filename of a file containing the list of patterns
to match on

=back

=head1 OPTIONS

=over 4

=item I<-f>

you can also specify the pattern list by passing in this option,
rather than specifying it as an argument.

=item I<-v>

print lines that don't match instead of lines that
do

=item I<-i>

case insensitive

=item I<-w>

add word boundaries around each pattern -- each pattern must match a word

=item I<-e>

exact matching.  the file contains strings to match, not patterns

=item I<--help>

Print a brief help message and exit.

=item I<--perldoc>

Print the perldoc page and exit.

=back

=head1 DESCRIPTION

MUCH slower than real fgrep.  but fgrep doesn't support large pattern
files and it isn't as easy to do whole word matching.

=cut

use strict;
use warnings 'all';
use Pod::Usage;
use Log::Log4perl qw(:levels);
use Getopt::Long;

# ----------------------

# default values
Log::Log4perl->easy_init($ERROR);
my $logger = Log::Log4perl->get_logger();

# parse command-line options
GetOptions( "reverse|v!"           => \my $REVERSE,
            "case_insensitive|i!"  => \my $CASE_INSENSITIVE,
            "pattern_is_word|w!"   => \my $PATTERN_IS_WORD,
	    "patternlist|file|f=s" => \my $PATTERNLIST,
	    "exact|e"              => \my $EXACT,
            "verbose"              => sub { $logger->level($DEBUG) },
          )
    or pod2usage();

# parse script arguments
if (!defined($PATTERNLIST)) {
    pod2usage("Wrong number of arguments") unless @ARGV >= 1;
    $PATTERNLIST = shift @ARGV;
}

# ----------------------

my %patterns;
my $wfd;
open($wfd, $PATTERNLIST)
    or $logger->logconfess("Can't open $PATTERNLIST: $? $! $@");
while(my $line = <$wfd>) {
    chomp($line);
    # skip blank lines and comments
    next if ($line =~ /^\s*$/o);
    next if ($line =~ /^\s*#/o);
    if ($PATTERN_IS_WORD) {
	# add word boundaries to the pattern
	$line = '\b' . $line . '\b';
    }
    $patterns{$line} = $line;
}
close($wfd) 
    or $logger->error("Can't close $PATTERNLIST: $? !$ $@");

# ----------------------

sub print_if_match ( $$$ ) {
    my ($patterns, $line, $reverse) = @_;
    foreach my $pattern (keys %$patterns) {
	my $match = 0;
	if ($EXACT) {
	    if ($line eq $pattern) {
                $match = 1;
            }
        } elsif ($CASE_INSENSITIVE) {
	    if ($line =~ /$pattern/i) {
		$match = 1;
	    }
	} else {
	    if ($line =~ /$pattern/) {
		$match = 1;
	    }
	}
	if ($match) {
	    print $line if (!$reverse);
	    return;
	}
    }
    print $line if ($reverse);
}

if (scalar(@ARGV) > 0) {
    foreach my $file (@ARGV) {
	my $fd;
        open($fd, $file);
	if (!$fd) {
	    $logger->error("Can't open $file: $? $! $@");
	    next;
	}
	while(my $line = <$fd>) {
	    print_if_match(\%patterns, $line, $REVERSE);
	}
	close($fd)
	    or $logger->error("Can't close $file: $? $! $@");
    }
} else {
    while(my $line = <>) {
	print_if_match(\%patterns, $line, $REVERSE);
    }
}

# ----------------------

__END__

=head1 AUTHOR

 Conan Yuan

=cut

