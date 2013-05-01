#!/usr/local/bin/perl -w

use strict;
use warnings 'all';
use Getopt::Long qw(:config pass_through);
use Log::Log4perl qw(:levels);
use List::MoreUtils qw(pairwise all firstidx);

# -----------------------------------------------

my $MAGIC = '#@desc';
Log::Log4perl->easy_init($ERROR);
my $LOGGER = Log::Log4perl->get_logger();

# -----------------------------------------------

sub main() {
    my ($cols, $files, $strs, $join_on) = get_options();
    if (scalar(@$strs) == 0) {
        return;
    }
    my $table;
    foreach my $file (@$files) {
        my $lines = read_files([$file], $strs);
        if (!defined($table)) {
            $table = $lines;
        } else {
            $table = join_tables($table, $lines, $join_on);
        }
    }
    print pretty(filter(transpose($table), $cols));
}

# -----------------------------------------------

sub default_files() {
    chomp(my $sdate = `date +%Y/%m/%d`);
    (my $date = $sdate) =~ s@/@@g;
    my $univ = "/data/optvol/eomm/universe/PROD/$date/underlying_universe.txt";
    $LOGGER->debug("Reading $univ");
    my $quotes = `ls -t /data/optvol/eomm/feed_dumps/PROD/$sdate/stock_quotes.* | head -1`;
    $LOGGER->debug("Reading $quotes");
    return ($univ, $quotes);
}

sub default_cols() {
    return qw(ticker spn desname bid ask shares_outstanding volume);
}

sub get_options() {

    GetOptions('verbose|v' => sub { $LOGGER->level($DEBUG) },
               'join|on=s'    => \my @join_on,
              );

    # Consume all options.  They just become the columns that we
    # should print.
    #
    # TODO: handle options with two hyphens
    # TODO: handle -- as "stop processing options"
    my @cols;
    while (scalar(@ARGV) > 0 && $ARGV[0] =~ /^-/) {
        push(@cols, substr(shift(@ARGV), 1));
    }

    # The user can end with as many files as they like.  We know they
    # are files if they are valid filenames.
    my @files;
    while (scalar(@ARGV) > 0 && -e $ARGV[-1]) {
        push(@files, pop(@ARGV));
    }
    if (scalar(@files) == 0) {
        @files = default_files();
        if (scalar(@cols) == 0) {
            @cols = default_cols();
        }
        if (scalar(@join_on) == 0) {
            @join_on = ('spn', 'ticker');
        }
    }

    return (\@cols, \@files, \@ARGV, \@join_on);
}

# -----------------------------------------------

# Returns a list of lists

sub read_files($$) {
    my ($files, $strs) = @_;

    # TODO: handle user specified patterns
    # TODO: handle compressed files
    my $patt = join('|', map {"^$_ "} ($MAGIC, @$strs));
    my @alllines;
    foreach my $file (@$files) {
        my $cmd = "egrep '$patt' $file";
        $LOGGER->debug("Running $cmd");
        my $text = `$cmd`;

        my @lines = split('\n', $text);
        my @flines;
        for (my $ii = 0; $ii < scalar(@lines); $ii++) {
            # Split on spaces, but allow backslash to escape spaces.
            my @flds = split('(?<!\\\) ', $lines[$ii]);

            # Remove backslash in front of spaces, those were
            # only for escaping
            foreach (@flds) { s/\\ / /g };

            # If this is the header, discard the $MAGIC keyword
            if (scalar(@flds) > 0 && $flds[0] eq $MAGIC) {
                shift(@flds);
            }

            # If we have multiple files, add the filename
            if (0 && scalar(@$files) > 1) {
                if ($ii == 0) {
                    unshift(@flds, 'FILE');
                } else {
                    unshift(@flds, $file);
                }
            }
            push(@flines, \@flds);
        }

        push(@alllines, @flines);
    }
    return \@alllines;
}

# -----------------------------------------------

# return the index of the first value in @$list that matches $val;
sub findidx($$) {
    my ($list, $val) = @_;
    return firstidx {$_ eq $val} @$list;
}

# convert a list of values into their corresponding indexes in a given
# list
sub indexes($$) {
    my ($list, $vals) = @_;
    return map {findidx($list, $_)} @$vals;
}

# given a list of indexs, return the corresponding values in @$list
sub take($$) {
    my ($list, $idxs) = @_;
    return map { $list->[$_] } @$idxs;
}

# The opposite of take
sub skip($$) {
    my ($list, $idxs) = @_;
    my @new;
    for (my $ii = 0; $ii < scalar(@$list); $ii++) {
        if (!contains($idxs, $ii)) {
            push(@new, $list->[$ii]);
        }
    }
    return @new;
}

sub arr_equal($$) {
    my ($arr1, $arr2) = @_;
    our ($a, $b);
    return all { $_ } pairwise { $a eq $b }  @$arr1, @$arr2;
}

sub join_tables($$$) {
    my ($table1, $table2, $on) = @_;
    # If nothing to join on, then just concatenate the tables
    if (!defined($on) || scalar(@$on) < 1 ||
        scalar(@$table1) < 1 || scalar(@$table2) < 1)
    {
        return [ @$table1, @$table2 ];
    }

    my $header1 = shift(@$table1);
    my $idxs1 = [indexes($header1, $on)];
    my $header2 = shift(@$table2);
    my $idxs2 = [indexes($header2, $on)];
    my @newtable = [@$header1, skip($header2, $idxs2)];
    foreach my $row1 (@$table1) {
        foreach my $row2 (@$table2) {
            if (arr_equal([take($row1, $idxs1)], [take($row2, $idxs2)])) {
                push(@newtable, [@$row1, skip($row2, $idxs2)]);
            }
        }
    }


    return \@newtable;
}

# -----------------------------------------------

# $intable should be a list of lists

sub transpose($) {
    my ($intable) = @_;
    my @outtable;

    while (1) {
        my $cont = 0;
        my $doprint = 1;
        my @output;

        for (my $ii = 0; $ii < @$intable; $ii++) {
            my $line = $intable->[$ii];
            my $val = '';
            if (scalar(@$line) > 0) {
                $cont = 1;
                $val = shift(@$line);
            }

            push(@output, $val);
        }
        push(@outtable, \@output);
        last unless $cont;
    }

    return \@outtable
}

# -----------------------------------------------

# return true iff $val is in @$list.
sub contains($$) {
    my ($list, $val) = @_;
    return scalar(grep { $_ eq $val } @$list) > 0;
}

# Filter rows whose first column matches one of the specified values
sub filter($$) {
    my ($table, $cols) = @_;
    if (@$cols > 0) {
        @$table = grep { contains($cols, $_->[0]) } @$table;

        # if we are extracting exactly one column, then don't
        # print the column name.
        if (scalar(@$cols) == 1) {
            foreach my $row (@$table) {
                shift(@$row)
                    if scalar(@$row) > 0;
            }
        }
    }
    return $table;
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
    my $output;
    foreach my $line (@$outtable) {
        for (my $ii = 0; $ii < scalar(@$line); $ii++) {
            $output .= sprintf("%-$widths[$ii]s ", $line->[$ii]);
        }
        $output .= "\n";
    }
    return $output;
}

# -----------------------------------------------

main();

# -----------------------------------------------
