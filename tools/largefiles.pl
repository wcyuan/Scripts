#!/usr/bin/env perl
#
# largefiles.pl
# @desc: list large files (wrapper around du)
#
# same as:
# du -Sam --time $args | perl -ane '$F[0] .= "M"; print join(" ", @F) . "\n" if (-f $F[-1])' | sort -rn | head -$top_n
#

# -----------------------------------------

use strict;
use Getopt::Long;
use warnings 'all';
use List::Util qw(min);
use Log::Log4perl qw(:levels);
use Statistics::Lite qw(median);

Log::Log4perl->easy_init($WARN);
my $LOGGER = Log::Log4perl->get_logger();

sub main() {
    my ($top_n, $relative, $in_kb,
        @dirs) = parse_command_line();

    my @all_lines;
    my $total = 0;
    my $start = time();

    # a: list both files and directories
    # S: for directories, show the size of the files in the directory,
    #    but not files in sub-directories
    # m: show sizes rounded to Megabytes
    # time: show last modified time of files or directories (for
    # directories, shows latest modification time of anything in the
    # directory)
    my $cmd = 'du -cSa --time';
    my $unit;
    if ($in_kb) {
        $cmd .= ' -k';
        $unit = 'K';
    } else {
        $cmd .= ' -m';
        $unit = 'M';
    }

    foreach my $dir (@dirs) {
        my @lines = run("$cmd $dir");

        # split
        @lines = map { [ split(' ', $_) ] } @lines;

        $total += pop(@lines)->[0];

        # files only
        @lines = grep { -f $_->[-1] } @lines;

        if ($relative) {
            $dir =~ s@/$@@;
            foreach my $line (@lines) {
                $line->[-1] =~ s@^$dir@.@;
            }
        }

        push(@all_lines, @lines);
    }

    # sort, largest first
    @all_lines = sort {$b->[0] <=> $a->[0] } (@all_lines);

    # print
    my $n_files = scalar(@all_lines);
    my $last = min($top_n-1, $#all_lines);
    foreach my $line (@all_lines[0..$last]) {
        if ($in_kb) {
            $line->[0] .= $unit;
        } else {
            $line->[0] .= $unit;
        }
        print join(' ', @$line) . "\n";
    }
    my $ave = sprintf('%0.2f', $n_files == 0 ? 0 : $total / $n_files);
    my $median = median(map { $_->[0] } @all_lines);
    my $time = time() - $start;
    print "$n_files files in $time seconds, total size ${total}${unit}, ave ${ave}${unit}, median ${median}${unit}\n";
}

# -----------------------------------------

sub parse_command_line() {
    my $top_n = 20;
    GetOptions('top_n|n=i'   => \$top_n,
               'relative|r!' => \my $relative,
               'verbose|v'   => sub { $LOGGER->level('DEBUG') },
               'kb|k'        => \my $in_kb,
              )
        or $LOGGER->logconfess("Invalid option");
    my @dirs = @ARGV;

    if (!defined($relative)) {
        if (scalar(@dirs) > 1) {
            $relative = 0;
        } else {
            $relative = 1;
        }
    }

    return ($top_n, $relative, $in_kb, @dirs);
}

sub run($) {
    my ($cmd) = @_;
    $LOGGER->debug($cmd);
    my $output = `$cmd`;
    return wantarray ? (split /\n/, $output) : $output;
}

# -----------------------------------------

main();

