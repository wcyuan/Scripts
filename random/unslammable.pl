#!/usr/local/bin/perl -w
#
# unslammable.pl
# @desc:  Short description.
#
# Conan Yuan, 20090621
#

=head1 NAME

unslammable.pl - Short description.

=head1 SYNOPSIS

  unslammable.pl [options] 

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

Scrabble slam is a game where every player has a bunch of letters (on
cards), and you start with a 4-letter word in the middle.  Each player
can put a letter on one of the word's existing letters, as long as it
makes a new word.  

So the question is, how many words can you start with that you can't
make any other words from?

=cut

use strict;
use warnings 'all';
use Pod::Usage;
use List::MoreUtils qw(uniq);

use Getopt::Long;

# ----------------------

# Default values
my $N_LETTERS = 4;

my @WORDLISTS = ('/usr/dict/words',
		 '4_letter_aus_scrabble_words.txt',
		 '4_letter_enable2k_words.txt');

# Parse any command-line options
GetOptions(  );

# Parse any script arguments
#pod2usage("Wrong number of arguments") unless @ARGV == 0;

my @words = @ARGV;

# ----------------------

sub get_hashes ( $ ) {
    my ($word) = @_;

    my @hashes;
    for (my $ii = 0; $ii < $N_LETTERS; $ii++) {
	my $hash = substr($word, 0, $ii) . "." . substr($word, $ii+1, $N_LETTERS-$ii-1);
	#print "$word -> $hash\n";
	$hash = lc $hash;
	push(@hashes, $hash);
    }
    return \@hashes;
}

# ----------------------

sub intersect ( @ ) {
    my (@lists) = @_;
    my $list1 = pop(@lists);
    # copy it...
    my @intersect = @$list1;
    foreach my $list (@lists) {
	@intersect = grep { $a = $_; scalar(grep {lc $_ eq lc $a} @$list) > 0 } @intersect;
    }
    return @intersect;
}

# ----------------------

my %DICT;
my %allwords;

foreach my $wordlist (@WORDLISTS) {
    my $rc = open(WORDS, $wordlist);
    if (!$rc) {
	warn("Can't open $wordlist: $? $! $@");
	next;
    }
    while (my $line = <WORDS>) {
	chomp($line);
	next if ($line =~ /^\s*#/);
	next if ($line =~ /^\s*$/);
	if (length($line) != $N_LETTERS) {
	    next;
	}

	push(@{$allwords{$wordlist}}, $line);
	push(@{$allwords{ALL}}, lc $line);
	my $hashes = get_hashes($line);
	foreach my $hash (@$hashes) {
	    push(@{$DICT{$wordlist}{$hash}}, $line);
	    push(@{$DICT{ALL}{$hash}}, lc $line);
	}
    }
    close(WORDS)
	or warn("Error closing $wordlist: $? $! $@");
}
# the union of all the lists
@{$allwords{ALL}} = uniq(@{$allwords{ALL}});
# the intersection of all the lists:
#@{$allwords{ALL}} = intersect(map {$allwords{$_}} @WORDLISTS);

# ----------------------

sub get_matches ( $$ ) {
    my ($word, $wordlist) = @_;

    my @matches;
    my $hashes = get_hashes($word);
    foreach my $hash (@$hashes) {
	my @these_matches = grep {lc($_) ne lc($word)} @{$DICT{$wordlist}{$hash}};
	push(@matches, @these_matches);
    }
    # only necessary for the ALL list
    @matches = uniq(@matches);
    return \@matches;
}

# ----------------------

if (scalar(@words) == 0) {
    foreach my $wordlist (@WORDLISTS, "ALL") {
	print "$wordlist:\n";
	foreach my $word (@{$allwords{$wordlist}}) {
	    my $matches = get_matches($word, $wordlist);
	    if (scalar(@$matches) == 0) {
		print $word . "\n";
		#print "$word -> " . join(',', @$matches) . "\n";
	    }
	}
    }
} else {
    foreach my $word (@words) {
	print "$word:\n";
	foreach my $wordlist (@WORDLISTS, "ALL") {
	    print "$wordlist:\n";
	    if (scalar(grep {lc $word eq lc $_} @{$allwords{$wordlist}}) == 0) {
		print("Can't find $word in $wordlist\n");
	    }
	    my $matches = get_matches($word, $wordlist);
	    print join(',', @$matches) . "\n";
	}
	print "---\n";
    }
}


# ----------------------

__END__

=head1 AUTHOR

 Conan Yuan

=cut

