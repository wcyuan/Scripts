#!/usr/local/bin/perl -w
#
# scrab.pl
# @desc:  Practice finding 7 and 8 letter words
#
# Conan Yuan, 20100212
#

=head1 NAME

scrab.pl - Practice finding 7 and 8 letter words

=head1 SYNOPSIS

  scrab.pl [options] 

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

Practice finding 7 and 8 letter words

=cut

use strict;
use warnings 'all';
use Pod::Usage;

use Getopt::Long;
use Log::Log4perl qw(:levels);

# ----------------------

Log::Log4perl->easy_init($ERROR);
my $logger = Log::Log4perl->get_logger();

# Default values


# Parse any command-line options
GetOptions( "score=s" => \my %score,
            "verbose" => sub { $logger->level($DEBUG) },
            "log_level=s" => sub { $logger->level($_[1]) },
          );

my @in_words = @ARGV;

# ----------------------

sub hashes($);
sub hashes($) {
    my ($word) = @_;

    if ($word !~ m/\?/) {
        return join('', sort split('', $word));
    }

    my @hashes;
    foreach my $letter ('a'..'z') {
        my $new_word = $word;
        $new_word =~ s/\?/$letter/;
        push(@hashes, hashes($new_word));
    }

    return @hashes;
}

# generate a random anagram
sub ranagram($) {
    my ($word) = @_;
    my $len = length($word);
    my @letters = split('', $word);
    my @permutation = (0..($len-1));
    for (my $ii = 0; $ii < $len; $ii++) {
        my $nth = int(rand($len));
        my $save = $permutation[$ii];
        $permutation[$ii] = $permutation[$nth];
        $permutation[$nth] = $save;
    }

    # randomly replace a letter with a blank...
    if (rand(2) > 1) {
        my $nth = int(rand($len));
        $letters[$nth] = "?";
    }

    return join('', map { $letters[$_] } @permutation);
}

# ----------------------

sub get_words() {
    my $wordfile = '/usr/dict/words';
    my @words;

    my $fd;
    open($fd, $wordfile)
        or $logger->logconfess("Can't open $wordfile: $? $! $@");
    while (my $line = <$fd>) {
        next unless ($line eq lc($line));
        chomp($line);
        next unless (length($line) == 7 || length($line) == 8);
        push(@words, $line);
    }
    close($fd)
        or $logger->error("Error closing $wordfile: $? $! $@");

    return \@words;
}

# ----------------------

my @board_links = ("t....................",
                   "n....................",
                   "o....................",
                   "ta...................",
                   "be...................",
                   "m....................",
                   "u....................",
                   ".e..3",
                   "..Bn.2",
                   "..Be.2",
                  );

my %scrabble_tile_values = ('a' => 1,
                            'b' => 3,
                            'c' => 3,
                            'd' => 2,
                            'e' => 1,
                            'f' => 4,
                            'g' => 2,
                            'h' => 4,
                            'i' => 1,
                            'j' => 8,
                            'k' => 5,
                            'l' => 1,
                            'm' => 3,
                            'n' => 1,
                            'o' => 1,
                            'p' => 3,
                            'q' => 10,
                            'r' => 1,
                            's' => 1,
                            't' => 1,
                            'u' => 1,
                            'v' => 4,
                            'w' => 4,
                            'x' => 8,
                            'y' => 4,
                            'z' => 10,
                            '?' => 0,
                           );


my %wwf_tile_values = ('a' => 1,
                       'b' => 3, # XXX
                       'c' => 4,
                       'd' => 2,
                       'e' => 1,
                       'f' => 4,
                       'g' => 3,
                       'h' => 3,
                       'i' => 1,
                       'j' => 8, # XXX
                       'k' => 5, # XXX
                       'l' => 2,
                       'm' => 3, # XXX
                       'n' => 2,
                       'o' => 1,
                       'p' => 4,
                       'q' => 10,
                       'r' => 1,
                       's' => 1,
                       't' => 1,
                       'u' => 2,
                       'v' => 5,
                       'w' => 4,
                       'x' => 8,
                       'y' => 3,
                       'z' => 10,
                       '?' => 0,
                      );

sub score_word($$) {
    my ($word, $board) = @_;
    my $tile_scores = \%wwf_tile_values;
    my $score = 0;
    if (!ref($word)) {
        my @letters = split('', $word);
        $word = \@letters;
    }

    if (!ref($board)) {
        my @board = split('', $board);
        $board = \@board;
    }

    my $word_mult = 1;
    for (my $ii = 0; $ii < scalar(@$word); $ii++) {
        my $l = lc $word->[$ii];
        my $b = $board->[$ii];
        if (!defined($b)) {
            return 0;
        }

        my $v = $tile_scores->{$l};
        if (!defined($tile_scores->{$l})) {
            $v = 1;
        }


        my $letter_mult = 1;
        if ($b =~ /[A-Z]/) {
            # uppercase letter are used to indicate letter multipliers
            $letter_mult = ord($b) - ord('A') + 1;
        } elsif ($b =~ m/\d/) {
            # numbers are used to indicate word multipliers
            $word_mult *= $b;
        } elsif ($b eq '.' || $b eq ' ') {
            # period means an empty space
            # nop
        } elsif ($b eq lc($b)) {
            # a lowercase letter means an existing tile, it has to
            # match the word given
            if ($b ne $l && $l ne '?') {
                return 0;
            }
        }
        $score += $v * $letter_mult;
        $logger->debug("letter $l, " . 
                       "board $b, " . 
                       "tile score " . ($tile_scores->{$l} || 0) . ", " . 
                       "letter mult $letter_mult, " . 
                       "letter-tile score $v, " . 
                       "word mult $word_mult, " . 
                       "score $score\n");
    }
    return $score *= $word_mult;
}

# returns a list of tuples where each tuple is [word, tiles, board, full_board_link, score]
sub find_matches( $$ ) {
    # not implemented
}

sub find_best_move ( $$ ) {
    my ($tiles, $board_links) = @_;
    foreach my $link (@$board_links) {
        # not implemented
    }
}


# ----------------------

my $words = get_words();

if (scalar(@in_words) > 0) {
    my %words_to_hashes;
    my %matches;
    foreach my $word (@in_words) {
        foreach my $h (hashes($word)) {
            push(@{$words_to_hashes{$word}}, $h);
            push(@{$matches{$h}{orig}}, $word);
        }
    }

    foreach my $word (@$words) {
        # assume these words have no question marks, so there can only
        # ever be a single hash.
        my $h = hashes($word);
        if (defined($matches{$h})) {
            push(@{$matches{$h}{words}}, $word);
        }
    }

    foreach my $hash (keys %matches) {
        next unless defined($matches{$hash}{words});

        print "$hash (";

        if (defined($matches{$hash}{orig})) {
            print join(',', @{$matches{$hash}{orig}});
        }
        print ") -> ";
        if (defined($matches{$hash}{words})) {
            print join(',', @{$matches{$hash}{words}});
        }
        print "\n";
    }
    exit;
} else {
    if (scalar(keys(%score)) > 0) {
        foreach my $word (keys(%score)) {
            print "$word \"$score{$word}\" " . score_word($word, $score{$word}) . "\n";
        }
        exit;
    }

    my $nth = int(rand(scalar(@$words)));
    my $word = $words->[$nth];
    my $ranagram = ranagram($word);
    $logger->debug("$word => $ranagram");
    print "$ranagram\n";
}

# ----------------------

__END__

=head1 AUTHOR

 Conan Yuan

=cut

