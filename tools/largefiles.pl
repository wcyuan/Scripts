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

Log::Log4perl->easy_init($WARN);
my $LOGGER = Log::Log4perl->get_logger();

sub main() {
    my ($top_n, $relative, $in_kb,
        @dirs) = parse_command_line();

    my @all_lines;
    foreach my $dir (@dirs) {
        # a: list both files and directories
        # S: for directories, show the size of the files in the directory,
        #    but not files in sub-directories
        # m: show sizes rounded to Megabytes
        # time: show last modified time of files or directories (for
        # directories, shows latest modification time of anything in the
        # directory)
        my $cmd = 'du -Sa --time';
        if ($in_kb) {
            $cmd .= ' -k';
        } else {
            $cmd .= ' -m';
        }
        my @lines = run("$cmd $dir");
        $dir =~ s@/$@@;

        # split
        @lines = map { [ split(' ', $_) ] } @lines;

        # files only
        @lines = grep { -f $_->[-1] } @lines;

        if ($relative) {
            foreach my $line (@lines) {
                $line->[-1] =~ s@^$dir@.@;
            }
        }

        push(@all_lines, @lines);
    }

    # sort, largest first
    @all_lines = sort {$b->[0] <=> $a->[0] } (@all_lines);

    # print
    my $last = min($top_n-1, $#all_lines);
    foreach my $line (@all_lines[0..$last]) {
        if ($in_kb) {
            $line->[0] .= "K";
        } else {
            $line->[0] .= "M";
        }
        print join(' ', @$line) . "\n";
    }
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

