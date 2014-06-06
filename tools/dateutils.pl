#!/usr/local/bin/perl -w
#

=head1 NAME

dateutils.pl - a place to hold date manipulation functions

=head1 SYNOPSIS

  dateutils.pl [options]

  Options:
    --help, -?        shows brief help message
    --perldoc         shows full documentation

=head1 ARGUMENTS

=over

=item I<arg1>

description

=back

=head1 OPTIONS

=over 4

=item I<--opt1>

description

=back

=head1 DESCRIPTION

=cut

use strict;
use warnings 'all';

use Carp;
use Date::Calc qw(Day_of_Week Delta_Days Add_Delta_Days);
use Getopt::Long;
use Log::Log4perl qw(:levels);
use Pod::Usage;
use Test::More;

# -------------------------------------------------------------------

Log::Log4perl->easy_init($ERROR);
my $LOGGER = Log::Log4perl->get_logger();

# -------------------------------------------------------------------

sub main() {
    getopts();
    run_tests();
}

sub getopts() {
    # parse command-line options
    GetOptions("verbose"      => sub { $LOGGER->level($DEBUG) },
               "log_level=s"  => sub { $LOGGER->level($_[1]) },
              )
        or pod2usage();

    # parse script arguments
    pod2usage("Wrong number of arguments") unless @ARGV == 0;

    return;
}

# -------------------------------------------------------------------

###
# Functions for manipulating yyyymmdd dates
###
sub get_year($) {
    my ($yyyymmdd) = @_;
    my $yyyy = substr($yyyymmdd, 0, -4);
    return $yyyy;
}

sub get_year_start($) {
    my ($year) = @_;
    return $year . '0101';
}

sub get_year_end($) {
    my ($year) = @_;
    return $year . '1231';
}

###
# Functions for converting to/from yyyymmdd and Date::Calc dates
###
sub to_yyyymmdd($$$) {
    my ($year, $month, $day) = @_;
    return sprintf('%d%02d%02d', $year, $month, $day);
}

sub from_yyyymmdd($) {
    my ($yyyymmdd) = @_;

    my $year = substr($yyyymmdd, 0, -4);
    my $mon  = substr($yyyymmdd, -4, -2);
    my $day  = substr($yyyymmdd, -2);

    return ($year, $mon, $day);
}

###
# Functions which run Date::Calc functions on yyyymmdd dates
###
sub days_between($$) {
    my ($from, $to) = @_;
    my ($from_year, $from_month, $from_day) = from_yyyymmdd($from);
    my ($to_year,   $to_month,   $to_day)   = from_yyyymmdd($to);
    return Delta_Days($from_year, $from_month, $from_day,
                      $to_year,   $to_month,   $to_day);
}

sub add_days($$) {
    my ($from, $to_add) = @_;
    my ($from_year, $from_month, $from_day) = from_yyyymmdd($from);
    ($from_year, $from_month, $from_day) =
        Add_Delta_Days($from_year, $from_month, $from_day, $to_add);
    return to_yyyymmdd($from_year, $from_month, $from_day);
}

###
# Functions which run Date::Calc functions and accept a filter
# function
###

sub general_days_between($$$);
sub general_days_between($$$) {
    my ($from, $to, $func) = @_;

    my ($from_year, $from_month, $from_day) = from_yyyymmdd($from);
    my ($to_year,   $to_month,   $to_day)   = from_yyyymmdd($to);

    if (Delta_Days($from_year, $from_month, $from_day,
                   $to_year,   $to_month,   $to_day) < 0) {
        return -1 * general_days_between($to, $from, $func);
    }

    my $days = 0;
    while (Delta_Days($from_year, $from_month, $from_day,
                      $to_year,   $to_month,   $to_day) > 0)
    {
        if ($func->($from_year, $from_month, $from_day)) {
            $days++;
        }
        ($from_year, $from_month, $from_day) =
            Add_Delta_Days($from_year, $from_month, $from_day, 1)
    }
    return $days;
}

sub general_add_days($$$) {
    my ($from, $to_add, $func) = @_;

    my ($from_year, $from_month, $from_day) = from_yyyymmdd($from);

    my $days = 0;
    my $incr = $to_add < 0 ? -1 : 1;
    while (abs($days) < abs($to_add))
    {
        if ($func->($from_year, $from_month, $from_day)) {
            $days++;
        }
        ($from_year, $from_month, $from_day) =
            Add_Delta_Days($from_year, $from_month, $from_day, $incr)
    }
    return to_yyyymmdd($from_year, $from_month, $from_day);
}

###
# Functions that filter on weekdays
###

sub is_weekday($$$) {
    my ($year, $month, $day) = @_;

    # 1 = Monday, ..., 6 = Saturday, 7 = Sunday
    my $dow = Day_of_Week($year, $month, $day);
    return ($dow != 6 && $dow != 7);
}

sub weekdays_between($$) {
    my ($from, $to) = @_;

    my $days = general_days_between($from, $to, \&is_weekday);

    $LOGGER->debug("weekdays_between from $from to $to = $days\n");

    return $days;
}

sub add_weekdays($$) {
    my ($from, $to_add) = @_;

    return general_add_days($from, $to_add, \&is_weekday);
}

###
# Functions for getting the current date
###
{
    my ($sec, $min, $hour, $mday, $mon, $year, $wday, $yday, $isdst);
    my $_initialized = 0;

    sub _init_current_date() {
        return if $_initialized;
        ($sec, $min, $hour, $mday, $mon, $year, $wday, $yday, $isdst) =
            localtime();
        $year += 1900;
        $mon++;
        $_initialized = 1;
    }

    sub get_current_year() {
        _init_current_date();
        return $year;
    }

    sub get_current_yyyymmdd() {
        _init_current_date();
        return to_yyyymmdd($year, $mon, $mday);
    }
}

###
# Functions for guessing that a string is part of a date
###

sub looks_like_year($) {
    my ($str) = @_;
    return ($str =~ m/^\d{4}$/ && $str > 1900);
}

sub looks_like_month($) {
    my ($str) = @_;
    return ($str =~ m/^\d{2}$/ && $str < 13);
}

sub looks_like_day($) {
    my ($str,) = @_;
    return ($str =~ m/^\d{2}$/ && $str < 32);
}

# -------------------------------------------------------------------

sub run_tests() {

    # Provide stack traces
    $SIG{__WARN__} = \&Carp::cluck;
    $SIG{__DIE__} = \&Carp::confess;

    BEGIN {
        plan tests => 12;
    }

    is(days_between(20130101, 20130102), 1);
    is(days_between(20130101, 20130103), 2);
    is(days_between(20130101, 20121231), -1);
    is(add_days(20130101, 1), 20130102);
    is(add_days(20121231, 1), 20130101);
    is(add_days(20130101, -1), 20121231);
    is(weekdays_between(20130101, 20130108), 5);
    is(weekdays_between(20130101, 20121226), -4);
    is(weekdays_between(20120228, 20120301), 2);
    is(add_weekdays(20130101, 5), 20130108);
    is(add_weekdays(20130101, -4), 20121226);
    is(add_weekdays(20120228, 2), 20120301);
}

# -------------------------------------------------------------------

main();

# -------------------------------------------------------------------

__END__

=head1 AUTHOR

 Conan Yuan

=cut

