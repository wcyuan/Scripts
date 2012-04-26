#!/usr/local/bin/perl -w
#
# bzgrep -h _price_size_default /data/cas/jsh/uoptslave/logs/log.commands.20120[34]* /data/cas/jsh/uoptslave/log.commands | cut -c 17-41,72-80 | bucket.pl -c 3 | less
#
# Prop#80614
#
# Each row is a date
#
# Each column is an integer number of seconds
#
# Each time a command took that many seconds to run, the value in that
# column is incremented.
#
# So this shows a sort of histogram, for each day, how many runs took
# 0-1 seconds, how many too 1-2 seconds, how many took 2-3 seconds,
# etc.
#

use strict;
use POSIX qw(floor);
use Text::Table;
use Getopt::Long;

my $idx = 0; # This is the column that contains the date
my $val = 1; # This is the column that contains the amount of time the
             # command took in seconds.
my $cap = 20;
GetOptions("idx_column|idx|i=i" => \$idx,
           "value_column|column|c=i" => \$val,
          )
    or die("Can't parse arguments");

sub bucket($) {
    my ($val) = @_;
    my $b = floor($val);
    $b = $cap if $b >= $cap;
    return $b;
}

my @data;
my %total;
while(my $line = <>) {
    my @F = split ' ', $line;
    $total{$F[$idx]}++;
    $data[bucket($F[$val])]{$F[$idx]}++; 
}

my $max = $#data;
my @buckets = (0..$max);
my $table = new Text::Table("id", "tot", @buckets);

foreach my $id (sort keys %total) { 
    $table->add($id, $total{$id}, 
                map { $data[$_]{$id} // '.' } @buckets);
}

print $table;
