#!/usr/local/bin/perl -w

use strict;
use warnings 'all';
use Getopt::Long qw(:config pass_through);
use Log::Log4perl qw(:levels);

# -----------------------------------------------

my $MAGIC = '#@desc';
Log::Log4perl->easy_init($ERROR);
my $LOGGER = Log::Log4perl->get_logger();

# -----------------------------------------------

sub main() {
    my ($cols, $files, $strs) = get_options();
    my $lines = read_files($files, $strs);
    pretty(transpose($lines, $cols, $strs));
}

# -----------------------------------------------

sub default_file() {
    chomp(my $date = `date +%Y%m%d`);
    return "/data/optvol/eomm/universe/PROD/$date/underlying_universe.txt";
}

sub get_options() {

    GetOptions('verbose|v' => sub { $LOGGER->level($DEBUG) });

    # Consume all options.  They just become the columns that we
    # should print.
    my @cols;
    while ($ARGV[0] =~ /^-/) {
        push(@cols, substr(shift(@ARGV), 1));
    }

    my @files;
    while (-e $ARGV[-1]) {
        push(@files, pop(@ARGV));
    }
    if (scalar(@files) == 0) {
        push(@files, default_file());
    }

    return (\@cols, \@files, \@ARGV);
}

# -----------------------------------------------

# Returns a list of lists

sub read_files($$) {
    my ($files, $strs) = @_;

    my $patt = join('|', map {"^$_ "} ($MAGIC, @$strs));
    my @lines;
    foreach my $file (@$files) {
        my $lines = `egrep '$patt' $file`;

        # Split on spaces, but allow backslash to escape spaces
        my @flines = map { [split('(?<!\\\) ', $_)] } split('\n', $lines);
        if (scalar(@$files) > 1) {
            if (scalar(@flines) > 0) {
                push(@{$flines[0]}, 'FILE');
                for (my $ii = 1; $ii < scalar(@flines); $ii++) {
                    push(@{$flines[$ii]}, $file);
                }
            }
            push(@lines, @flines);
        } else {
            @lines = @flines;
        }
    }
    return \@lines;
}

# -----------------------------------------------

# $intable should be a list of lists

sub transpose($$$) {
    my ($intable, $cols, $strs) = @_;
    my @outtable;

    while (1) {
        my $cont = 0;
        my $doprint = 1;
        my @output;
        if (@$cols > 0) {
            unless (scalar(@$intable) > 0 && scalar(@{$intable->[0]}) > 0 &&
                    scalar(grep { $_ eq $intable->[0][0] } @$cols) > 0) {
                $doprint = 0;
            }
        }

        for (my $ii = 0; $ii < @$intable; $ii++) {
            my $line = $intable->[$ii];
            my $val = '';
            if (scalar(@$line) > 0) {
                $cont = 1;
                $val = shift(@$line);
                if ($val eq $MAGIC) {
                    $val = shift(@$line);
                }
                $val =~ s/\\ / /g;
            }

            # if we are extracting exactly one column, then don't
            # print the column name.
            unless ($doprint && @$cols == 1 && $ii == 0) {
                push(@output, $val);
            }
        }
        push(@outtable, \@output)
            if $doprint;
        last unless $cont;
    }

    return \@outtable
}

# -----------------------------------------------

# pretty

sub pretty($) {
    my ($outtable) = @_;
    my @widths;
    foreach my $line (@$outtable) {
        for (my $ii = 0; $ii < scalar(@$line); $ii++) {
            if (!defined($widths[$ii]) || length($line->[$ii]) > $widths[$ii]) {
                $widths[$ii] = length($line->[$ii]);
            }
        }
    }
    foreach my $line (@$outtable) {
        for (my $ii = 0; $ii < scalar(@$line); $ii++) {
            printf("%-$widths[$ii]s ", $line->[$ii]);
        }
        print "\n";
    }
}

# -----------------------------------------------

main();

# -----------------------------------------------
