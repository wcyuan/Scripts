#!/usr/local/bin/perl -w
#
# $Id: cw.pl,v 1.9 2009/04/13 18:37:52 yuanc Exp yuanc $
# $Source: /u/yuanc/testbed/perl/random/RCS/cw.pl,v $
#
# cw.pl
# @desc:  a script for reading Across Lite crossword files
#
# Download from http://world.std.com/~wij/puzzles/cru/
#
# or Search for Cru Cryptics from NY Times forum participants
#
# Conan Yuan, 20080604
#

=head1 NAME

cw.pl - a script for reading Across Lite crossword files

=head1 SYNOPSIS

  cw.pl [options] <file>

  Options: 
    --help, -?        shows brief help message
    --perldoc         shows full documentation

  See also Deshaw::Getopt::Long for complete standard options list.

=head1 ARGUMENTS

=over

=item I<file>

the input file

=back

=head1 OPTIONS

=over 4

=item I<--help>

Print a brief help message and exit.

=item I<--perldoc>

Print the perldoc page and exit.

=back

=head1 DESCRIPTION

a script for reading Across Lite crossword files

=cut

use strict;
use warnings 'all';
use Pod::Usage;
use File::Basename qw(basename);
use File::Temp  qw(tempdir);

use Deshaw::Base;
use Deshaw::Getopt::Long;
use Deshaw::Util::Log;
use Deshaw::Util::SmartOpen;
use Deshaw::Constants::Getopt qw(FLAG_no_write);

# ----------------------

# Default values

# a regexp that matches the characters in the puzzle file that we don't recognize
my $SEPARATOR_RE = '[^\w\s[:punct:]]';

# the character used to represent an open box in the actual puzzle
my $BLANK_CHAR = '-';

# the character used to represent a black square in the actual puzzle
my $BLACK_SPACE_CHAR = '.';

# a regexp to match the representation of the actual puzzle within the puzzle file
my $PUZZLE_RE = '\\' . $BLANK_CHAR;

# a regexp to match clues in the puzzle file.  
my $CLUE_RE = '\([\d\,\-]+\)$';


# Parse any command-line options
GetOptions("all" => \my $print_all,
	   "rest" => \my $print_rest,
	   "sol" => \my $print_solution,
	   "print" => \my $send_to_printer,
	  );

# Parse any script arguments
pod2usage("Wrong number of arguments") unless @ARGV > 0;
my @files = @ARGV;


# ----------------------

sub puzzle_string ( $$ ) {
    my ($puzzle, $filename) = @_;
    my $output;

    my $length = length($puzzle);
    # assume that the puzzle is square!
    my $row = sqrt($length);
    if ($row != int($row)) {
	warning("$filename: Puzzle is not square!  $length");
    }
    $row = int(sqrt($length));

    my @entries;

    for (my $tot = 0; $tot < $length; $tot += $row) {
	$output .= "\n";
	$output .= sprintf("%3d ", ($tot+1));
	# Check to see what 
	for (my $col = 0; $col < $row; $col++) {
	    my $this_space = 				  substr($puzzle, $tot+$col, 1);
	    my $left       = $col > 0 			? substr($puzzle, $tot+$col-1, 1) : "";
	    my $right      = $col < $row-1 		? substr($puzzle, $tot+$col+1, 1) : "";
	    my $above      = $tot > 0 			? substr($puzzle, $tot+$col-$row, 1) : "";
	    my $below      = $tot+$col+$row < $length 	? substr($puzzle, $tot+$col+$row, 1) : "";

	    # is this the beginning of an ACROSS clue?
	    # Yes, if: 
	    # This isn't the last space on the row
	    # This is a blank
	    # The value to the left is a blank, and 
	    # The value to the right is non-blank or this is the first column in the row
	    if ($col+1 < $row &&
		$this_space ne $BLACK_SPACE_CHAR &&
		$right ne $BLACK_SPACE_CHAR &&
		($col == 0 || $left eq $BLACK_SPACE_CHAR)) {
		push(@entries, $tot+$col+1 . " A");
	    }

	    # is this the beginning of a DOWN clue?
	    # Yes, if: 
	    # This isn't the last space on the column
	    # This is a blank
	    # The value below is a blank, and 
	    # The value above is non-blank or this is the first row in the column
	    if ($tot+$col+$row < $length &&
		$this_space ne $BLACK_SPACE_CHAR &&
		$below ne $BLACK_SPACE_CHAR &&
		($tot == 0 || $above eq $BLACK_SPACE_CHAR)) {
		push(@entries, $tot+$col+1 . " D");
	    }

	    if ($this_space eq $BLANK_CHAR) {
		$output .= "__";
	    } elsif ($this_space eq $BLACK_SPACE_CHAR) {
		$output .= "##";
	    } else {
		$output .= $this_space . " ";
	    }
	    $output .= " ";
	}
	$output .= "\n";
    }
    return wantarray ? ($output, \@entries) : $output;
}

#
# The file looks like this:
#
# YgACROSS&DOWN jJ	��+Ѷ�1.3 im7z, Sun, Jun 0   OGCMYDQ.OSKIZEDY.N.B.H.O.F.N.OFBQOC.BPRQFNEJEX.G.W.S.Q.U.W.LMXWWONK.UGXMJISX.M...B...V.A.USXGJBADHAOA....T.H.V.L.T.G.U.I....KQFIGACSFQUG.E.O...V...N.QDKJFHZQ.YXBYXSGB.H.R.Y.U.R.W.YRWWWZHHSW.DJWDQK.V.F.R.S.O.D.EOVWJWSM.YTETBGL-------.--------.-.-.-.-.-.-.------.----------.-.-.-.-.-.-.--------.--------.-...-...-.-.------------....-.-.-.-.-.-.-.-....------------.-.-...-...-.--------.--------.-.-.-.-.-.-.----------.------.-.-.-.-.-.-.--------.-------NY Times, Sun, Jun 01, 2008  CRYPTIC CROSSWORD Fraser Simpson / Will Shortz � 2008, The New York Times Crazy hosts so like the Shriners (7) Corrected overdose if I brought in medication (8) Crystal gazer describes distant sailor (8) Nine musicians, not one on time (5) English prime minister ailing after religious service (9) Uses iodine in some computers (7) Varsity players had breakfast in the morning (1-4) Actor Cole harbors not much hope (9) Ugly alien has head of household take a breath (6) Pair of seats in Parisian cars (6) Darn, I mistakenly let out the water (5) Found in bureau near the door (9) Desperate French caper (7) Customarily never shows Ms. Monroe (7) Power chosen by Rhode Island metropolis (11) Remaining water vessel possibly cut up (4,5) Bank's site reorganized work to be completed (2-7) See great new way to travel cheaply (8) Announcement at this spot by New Testament disciple (8) Considered sandwich seller reprimanded (11) Research center considering a tar pit locale (2,4) Doctor spread curtains (6) Waste a sporting award (7) Remain repulsed about eastern poet (5) The lining irritated? Hah! (2,5) Country music may have this sharpness about Pres. Bush (5) Discount stocks for unprincipled person (9) Wow � a labyrinth (5) Facilitates reciting a chapter in a dermatology text? (7) F.B.I. agents infiltrating prepared division (7)  
#
# It looks like the beginning is some garbage we don't understand.  
#
# Then at some point they have a 225 character string made up of
# letters and periods.  This is probably the encoded solution.
#
# Right after that, there is a 225 character string made up of dashes
# and periods.  The periods are in the same places as in the previous
# string.  This probably encodes the form puzzle.  
#
# Then there is some information about the puzzle, like the title and authors and stuff.  
#
# Finally, you get the clues.  
#
sub file_to_string ( $ ) {
    my ($filename) = @_;
    my $output = "______    $filename     ______\n";

    my $fd = smart_open($filename)
	or panic("Can't open $filename: $? $! $@");
    chomp(my $line = join('', <$fd>));
    close($fd)
	or panic("Can't close $filename: $? $! $@");

    # split on weird characters: anything that isn't a 
    # word, whitespace, or punctuation
    my @fields = split(/$SEPARATOR_RE/, $line);

    if ($print_all) {
	foreach my $f (@fields) {
	    $output .= $f . "\n"
	}
    }

    #
    # Skip junk before the puzzle
    #
    while (scalar(@fields) > 0 && $fields[0] !~ /$PUZZLE_RE/) {
	my $skip = shift(@fields);
	debug("$filename: skipping $skip\n");
    }


    #
    # Get the puzzle
    #
    if (scalar(@fields) <= 0) {
	panic("Can't read puzzle $filename");
    }
    my $puzzle = shift(@fields);
    # The puzzle string we got is actually the solution and the puzzle
    # concatenated together, then a bunch of stuff we don't care
    # about.  The solution is made up of letters and periods.  The
    # puzzle is made up of dashes and periods.  The stuff we don't
    # care about probably doesn't have any dashes.  So the stuff we
    # don't care about is the string that begins with the first
    # non-period, non-dash that occurs after a string made up of only
    # periods and dashes.
    $puzzle =~ s/^(.*)(\-[\-\.]*)([^\.\-].*)$/$1$2/;
    my $length = length($puzzle) / 2;
    my $solution = substr $puzzle, 0, $length;
    $puzzle = substr $puzzle, $length, $length;

    my ($puz_string, $entries) = puzzle_string($puzzle, $filename);
    $output .= $puz_string;

    #
    # Skip junk between the puzzle and the clues
    #
    while (scalar(@fields) > 0 && $fields[0] !~ /$CLUE_RE/) {
	my $skip = shift(@fields);
	debug("$filename skipping $skip\n");
    }


    #
    # Get the clues
    #
    my @clues;
    while (scalar(@fields) > 0) {
	if ($fields[0] =~ /$CLUE_RE/) {
	    push(@clues, shift(@fields));
	} elsif (scalar(@fields) > 1 && $fields[1] =~ /$CLUE_RE/) {
	    # some of the characters in the clues are control characters.  For
	    # example, in "Wow \227 a labyrinth", the \227 is a control
	    # character, but it probably indicates an exclamation point or
	    # something.
	    #
	    # This will work if there is one control character in the
	    # clue, but not if there are more
	    my $clue = shift(@fields);
	    $clue   .= shift(@fields);
	    push(@clues, $clue);
	} else {
	    last;
	}
    }
    if (scalar(@$entries) != scalar(@clues)) {
	warning("$filename: Different number of blanks and clues: " . scalar(@$entries) . " " . scalar(@clues));
    }


    #
    # Get the rest.  It may include an explanation of the solution.  
    #
    my @rest = @fields;

    $output .= "\n";
    my $entry = 0;
    foreach my $c (@clues) {
	$output .= sprintf "%6s: ", $entries->[$entry];
	$output .= $c . "\n";
	$entry++;
    }
    if ($print_rest) {
	foreach my $r (@rest) {
	    $output .= $r . "\n";
	}
    }

    if ($print_solution) {
	$output .= "\n";
	$output .= puzzle_string($solution, $filename);
    }

    return $output;
}


my $file_string = join("\f\n", map { file_to_string($_) } @files);

if ($send_to_printer) {
    my $cleanup = FLAG_no_write() ? 0 : 1;
    my $TMP_DIR = tempdir(CLEANUP => $cleanup, DIR => "/tmp");
    my $print_file = $TMP_DIR . "/" . basename($files[0]);
    my $outfd = smart_open($print_file, "w")
	or panic("Can't write to $print_file: $? $! $@");
    print $outfd $file_string;
    close($outfd)
	or error("Can't close $print_file: $? $! $@");
    my $cmd = "enscript -2rGh -DDuplex:true -d lp-23e $print_file";
    debug($cmd);
    if (!FLAG_no_write()) {
	my $rc = system($cmd);
	if ($rc != 0) {
	    warning("Non zero return code running: \"$cmd\", $rc");
	}
    } else {
	print "leaving $print_file\n";
    }
} else {
    print $file_string;
}

# ----------------------

__END__

=head1 AUTHOR

 Conan Yuan
 $Revision: 1.9 $
 $Source: /u/yuanc/testbed/perl/random/RCS/cw.pl,v $

=cut

