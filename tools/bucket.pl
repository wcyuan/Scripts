#!/usr/local/bin/perl -w
#
#
# bzgrep -h _price_size_default /data/cas/jsh/uoptslave/logs/log.commands.20120[34]* /data/cas/jsh/uoptslave/log.commands | perl -ane 'print substr($_,16,25), " ", substr($_,71,9), "\n"' | bucket.pl
#
# bzgrep -h guas::public /data/cas/jsh/uoptslave/logs/log.commands.20120[34]* /data/cas/jsh/uoptslave/log.commands | perl -ane 'print substr($_,16,25), " ", substr($_,71,9), "\n"' | bucket.pl
#
#
# The input should look like this:
#
# 20120223 06:30:33.322 EST   30.772 
# 20120223 06:30:33.322 EST   31.752 
# 20120223 06:32:12.536 EST   19.591 
# 20120223 06:32:44.017 EST    0.496 
# 20120223 06:33:07.912 EST    0.399 
# 20120223 06:33:08.440 EST    0.121 
# 20120223 06:33:08.872 EST    0.162 
# 20120223 06:33:10.636 EST    0.105 
# 20120223 06:33:11.222 EST    0.118 
# 20120223 06:33:11.451 EST    0.101 
#
#
# The output should look lik this:
# id       tot  0    1   2  3  4  5  6  7  8 9 10 11 12 13 14 15 16 17 18 19 20
# 20120223  948  762 123 31 13  4  2  3  1 . . .  .  .  1  .  2  .  .  .  1   5
# 20120224 1199 1037  95 41 10  1  3  2  3 1 . .  .  .  .  .  1  .  .  .  .   5
# 20120227 1001  829  97 45 10  2  3  2  2 2 1 .  2  1  .  .  1  .  .  1  .   3
# 20120228  944  753 109 55  8  2  2  2  1 . 1 2  1  1  .  .  1  .  .  1  .   5
# 20120229 1200 1003 110 58  7  2  3  1 .  3 2 2  1  .  1  1  .  .  1  1  .   4
# 20120301 1327 1102 121 43  9  7 11 12  5 1 1 1  .  3  1  2  .  .  1  .  .   7
# 20120302  905  735  66 33 15  5 15  8  3 3 3 3  1  1  .  2  .  .  2  .  1   9
# 20120305 1140  900 131 64  9 10  4 .   2 3 2 .  3  3  4  .  .  2  .  .  .   3
# 20120306 1082  866 159 12  7  9  4  5  2 4 1 1  3  .  .  .  .  1  .  .  1   7
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
use Scalar::Util qw(looks_like_number);

sub main() {
    my ($idx, 
        $val, 
        $cap,
       ) = parse_command_line();
    my ($data, $total) = collect_data($idx, $val, $cap);
    print_data($data, $total);
}

sub parse_command_line() {

    my $idx =  0;          # This is the column that contains the date
    my $val = -1; # This is the column that contains the amount of time the
    # command took in seconds.
    my $cap = 15;

    GetOptions("idx_column|idx|i=i"   => \$idx,
               "value_column|val|v=i" => \$val,
               "cap|c=i"              => \$cap,
              )
        or die("Can't parse arguments");

    return ($idx, $val, $cap);
}

sub bucket($$) {
    my ($val, $cap) = @_;
    
    my $b = floor($val);
    $b = $cap if $b >= $cap;
    return $b;
}

sub collect_data($$$) {
    my ($id_idx, $val_idx, $cap) = @_;
    my @data;
    my %total;
    while(my $line = <>) {
        my @F = split ' ', $line;

        my $id  = $F[$id_idx];
        my $val = $F[$val_idx];

        if (!defined($id) || 
            !looks_like_number($id) ||
            !defined($val) ||
            !looks_like_number($val)) 
        {
            warn("Skipping malformed line $line");
            next;
        }

        $total{$id}++;
        $total{all}++;
        my $b = bucket($val, $cap);
        $data[$b]{$id}++; 
        $data[$b]{all}++; 
    }
    return (\@data, \%total);
}

sub get_data($$$$;$) {
    my ($data, $total, $bucket, $id, $as_percent) = @_;

    my $default = '.';
    if ($as_percent) {
        if ($total->{$id} == 0) {
            return 0;
        }
        $default = 0;
    }

    my $val = $data->[$bucket]{$id};
    $val //= $default;

    if ($as_percent) {
        $val /= $total->{$id};
        $val *= 100;
        $val = sprintf('%.2g%%', $val);
    }

    return $val;
}

sub print_data($$) {
    my ($data, $total) = @_;
    my $max = $#{$data};
    my @buckets = (0..$max);
    my $table = new Text::Table("id", "tot", @buckets);

    foreach my $id (sort grep {$_ ne 'all'} keys %$total) {
        $table->add($id, $total->{$id}, 
                    map { 
                        get_data($data, $total, $_, $id) 
                    } @buckets);
    }

    # show percentages when summed up over all ids
    $table->add('all', $total->{all}, 
                map {
                    get_data($data, $total, $_, 'all', 1)
                } @buckets);

    print $table;
}

# ------------------------------------------------

main();

# ------------------------------------------------
