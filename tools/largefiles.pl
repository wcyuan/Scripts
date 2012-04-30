#!/usr/bin/env perl
#
# largefiles.pl
# @desc: list large files (wrapper around du)
#

# -----------------------------------------

use strict;
use Getopt::Long;
use warnings 'all';
use Log::Log4perl qw(:levels);
Log::Log4perl->easy_init($WARN);
my $LOGGER = Log::Log4perl->get_logger();

sub main() {
    my ($args, $top_n) = parse_command_line();

    # a: list both files and directories
    # S: for directories, show the size of the files in the directory,
    #    but not files in sub-directories
    # m: show sizes rounded to Megabytes
    # time: show last modified time of files or directories (for
    # directories, shows latest modification time of anything in the
    # directory)
    my @lines = run("du -Sam --time $args");

    # split
    @lines = map { [ split(' ', $_) ] } @lines;

    # files only
    @lines = grep { -f $_->[-1] } @lines;

    # sort, largest first
    @lines = sort {$b->[0] <=> $a->[0] } (@lines);

    # print
    foreach my $line (@lines[0..($top_n-1)]) {
        $line->[0] .= "M";
        print join(' ', @$line) . "\n";
    }
}

# -----------------------------------------

sub parse_command_line() {
    my $top_n = 20;
    GetOptions('top_n|n=i' => \$top_n)
        or $LOGGER->logconfess("Invalid option");
    my $args = join(' ', @ARGV);
    return ($args, $top_n);
}

sub run($) {
    my ($cmd) = @_;
    $LOGGER->debug($cmd);
    my $output = `$cmd`;
    return wantarray ? (split /\n/, $output) : $output;
}

# -----------------------------------------

main();

