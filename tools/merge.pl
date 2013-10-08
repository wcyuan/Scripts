#!/usr/local/bin/perl -w
#############################################################
###
### merge.pl
###
use Carp;
use strict;
use Getopt::Std;
use vars qw($opt_n $opt_f $opt_p);
$ENV{USAGE} = "usage: $0 <filename>*\n";
getopts("n:f") || die $ENV{USAGE};

my ($offset) = defined($opt_n) ? $opt_n : 0;
my ($use_filenames) = defined($opt_f);
my ($DELIM) = ":";
my ($OUTFD) = *STDOUT;
my (@fhs, @fns);

my $stillgoing=1;

foreach my $file (@ARGV) {
    local *FH;
    open *FH, $file or croak "Couldn't open $file: $!\n";
    push @fhs, *FH;
    push @fns, $file;
}

while ($stillgoing) {
    $stillgoing=0;
    my ($file_n) = 0;
    for (my $ii = 0; $ii < scalar(@fhs); $ii++) {
	my ($fh) = $fhs[$ii];
	my ($fn) = $use_filenames ? $fns[$ii] . $DELIM : "";
	$file_n++;
	if ($file_n == 1 && $offset > 0) {
	    --$offset; next;
	} elsif ($file_n != 1 && $offset < 0) {
	    ++$offset; next;
	}
	if (!eof($fh)) {
	    print $OUTFD $fn . <$fh>;
	    $stillgoing=1;
	}
    }
}

foreach my $fh (@fhs) { close($fh); }
