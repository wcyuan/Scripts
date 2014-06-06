#!/usr/local/bin/perl -w
#
# ovd.pl
# @desc:  print out information about my schedule
#
# Conan Yuan
#

=head1 NAME

ovd.pl - print out information about my schedule

=head1 SYNOPSIS

  ovd.pl [start year] [end year]

  Options:
    --help, -?        shows brief help message
    --perldoc         shows full documentation

=cut

# -------------------------------------------------------------------
# Includes

use strict;
use Date::Calc qw(Day_of_Week Delta_Days Add_Delta_Days);
use Getopt::Long qw(GetOptions);
use Log::Log4perl qw(:levels);
use Pod::Usage;
use Scalar::Util qw(looks_like_number);
use Text::Table;

# -------------------------------------------------------------------
# Defaults

Log::Log4perl->easy_init($ERROR);
my $LOGGER = Log::Log4perl->get_logger();

my $INOUT_SCHEDULE = $ENV{HOME} . "/usr/crontab/inoutschedule";

my @COMPUTED = qw(PTO PTO_AVAIL PTO_REM ALL_REASONS);
my @PTO_REASONS = qw(OVD OPD ORD);

# You start with 17 days PTO.  After working for 2 years (or if you
# make VP), you get 22.  After working 10 years (or if you make SVP or
# MD), you get 27 days).
my @PTO_ALLOWED = ([10, 27], [2, 22], [0, 17]);

my $START = 2000;

# -------------------------------------------------------------------
# Main

sub main() {
    my ($year, $end_year) = parse_command_line();

    if (defined($year) && $year eq "status") {
        print inout_status($INOUT_SCHEDULE, $end_year) . "\n";
        return;
    }

    my $table = inout_table($INOUT_SCHEDULE, $year, $end_year);
    print $table;
}

# -------------------------------------------------------------------
# Command line
#

sub parse_command_line() {

    GetOptions( "verbose|v" => sub { $LOGGER->level($DEBUG) },
              )
        or pod2usage();

    if (scalar(@ARGV) > 2) {
        pod2usage();
    }
    my ($year, $end_year) = @ARGV;
    return ($year, $end_year);
}

# -------------------------------------------------------------------
#
# Date Manipulation
#

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
# Functions using Date::Calc dates, or converting to/from yyyymmdd and
# Date::Calc dates
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

sub days_between($$) {
    my ($from, $to) = @_;
    my ($from_year, $from_month, $from_day) = from_yyyymmdd($from);
    my ($to_year,   $to_month,   $to_day)   = from_yyyymmdd($to);
    return Delta_Days($from_year, $from_month, $from_day,
                      $to_year,   $to_month,   $to_day);
}

sub is_weekday($$$) {
    my ($year, $month, $day) = @_;

    # 1 = Monday, ..., 6 = Saturday, 7 = Sunday
    my $dow = Day_of_Week($year, $month, $day);
    return ($dow != 6 && $dow != 7);
}

sub general_days_between($$$) {
    my ($from, $to, $func) = @_;

    my ($from_year, $from_month, $from_day) = from_yyyymmdd($from);
    my ($to_year,   $to_month,   $to_day)   = from_yyyymmdd($to);

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

sub weekdays_between($$) {
    my ($from, $to) = @_;

    my $days = general_days_between($from, $to, \&is_weekday);

    $LOGGER->debug("weekdays_between from $from to $to = $days\n");

    return $days;
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

# -------------------------------------------------------------------
# Functions for reading the schedule
#

sub read_inout_schedule($) {
    my ($inout_schedule) = @_;
    my @retval;
    my $last_to;
    open (SCHEDULE, $inout_schedule)
        or $LOGGER->logconfess("Can't open $inout_schedule: $? $! $@");
    while (my $line = <SCHEDULE>) {
        next if $line =~ m/^\s*#/o;
        next if $line =~ m/^\s*$/o;
        my ($date_range, $mode, $reason) = split ' ', $line;
        my ($from, $to) = split "-", $date_range;
        if (!defined($to)) {
            print "$line\n";
        }
        if ($to < $from) {
            $LOGGER->warn("Invalid date range: $line");
        }
        if (defined($last_to) && $from <= $last_to) {
            $LOGGER->warn("Date range overlaps previous date range: $line");
        }
        $last_to = $to;

        push(@retval, [$from, $to, $mode, $reason]);
    }
    close(SCHEDULE)
        or $LOGGER->error("Error closing $inout_schedule: $? $! $@");
    return @retval;
}

# Get today's status
sub inout_status($;$) {
    my ($schedule, $date) = @_;
    if (!defined($date)) {
        $date = get_current_yyyymmdd();
    }
    # default status
    my $status = "in";
    my $seen = 0;
    foreach my $info (read_inout_schedule($schedule)) {
        my ($start_date, $end_date, $stat) = @$info;
        if ($date >= $start_date && $date <= $end_date) {
            if ($seen) {
                $LOGGER->warn("$date is part of two date ranges.  " .
                              "Using $stat instead of $status");
            }
            $seen = 1;
            $status = $stat;
        }
    }
    return $status;
}

sub pto_allowed($) {
    my ($year) = @_;
    my $nyears = $year - $START;
    foreach my $pair (@PTO_ALLOWED) {
        my ($n, $pto) = @$pair;
        if ($nyears >= $n) {
            return $pto;
        }
    }
}

# Group statuses by reason.  Helper for inout_table.
sub inout_by_reason($$$) {
    my ($schedule, $first, $last) = @_;

    my %reasons;
    foreach my $info (read_inout_schedule($schedule)) {
        my ($from, $to, $mode, $this_reason, $from_date, $to_date) = @$info;
        next if $mode eq "IN";
        next if ($to < $first);
        next if ($from > $last);
        $from = $first if ($from < $first);
        $to = $last if ($to > $last);

        # both from and to are inclusive, so we have to add one to daysbetween
        my $days = weekdays_between($from, $to) + 1;
        my $to_year = get_year($to);
        my $from_year = get_year($from);
        if ($to_year != $from_year) {
            my $from_days =
                weekdays_between($from, get_year_end($from_year)) + 1;
            $reasons{$this_reason}{$from_year} += $from_days;
            my $to_days = weekdays_between(get_year_start($to_year), $to) + 1;
            $reasons{$this_reason}{$to_year} += $to_days;
        } else {
            $reasons{$this_reason}{$from_year} += $days;
        }
    }

    #
    # Computed Reasons
    #

    # ALL_REASONS
    foreach my $reason (grep {$_ ne 'ALL_REASONS'} keys(%reasons)) {
        foreach my $year (keys(%{$reasons{$reason}})) {
            $reasons{ALL_REASONS}{$year} += $reasons{$reason}{$year};
        }
    }

    # PTO (paid time off)
    foreach my $year (keys(%{$reasons{ALL_REASONS}})) {
        $reasons{PTO}{$year} = 0;
        foreach my $reason (@PTO_REASONS) {
            if (exists($reasons{$reason}) &&
                defined($reasons{$reason}{$year}))
            {
                $reasons{PTO}{$year} += $reasons{$reason}{$year};
            }
        }
        $reasons{PTO_AVAIL}{$year} = pto_allowed($year);
        $reasons{PTO_REM}{$year} = pto_allowed($year) - $reasons{PTO}{$year};
    }

    #
    # Computed Years
    #

    # ALL_YEARS
    foreach my $reason (keys(%reasons)) {
        foreach my $year (grep {$_ ne 'ALL_YEARS'} keys(%{$reasons{$reason}})) {
            $reasons{$reason}{ALL_YEARS} += $reasons{$reason}{$year};
        }
    }

    # AVERAGE
    my $nyears = scalar(keys(%{$reasons{ALL_REASONS}})) - 1;
    if ($nyears > 0) {
        foreach my $reason (keys(%reasons)) {
            $reasons{$reason}{AVERAGE} =
                sprintf("%.2f", $reasons{$reason}{ALL_YEARS} / $nyears);
        }
    }

    return \%reasons;
}

sub real_reason($) {
    my ($reason) = @_;
    return scalar(grep {$reason eq $_} @COMPUTED) == 0;
}

sub inout_table($;$$) {
    my ($schedule, $year, $end_year) = @_;
    if (defined($year)) {
        if (!looks_like_number($year)) {
            $LOGGER->logconfess("Invalid year: $year");
        }
    } else {
        $year = get_current_year();
    }
    if (!defined($end_year)) {
        $end_year = $year;
    }

    my $reasons = inout_by_reason($schedule,
                                  get_year_start($year),
                                  get_year_end($end_year));

    my @years = sort keys(%{$reasons->{ALL_REASONS}});
    my $n_years = $end_year - $year + 1;
    if ($n_years == 1) {
        @years = grep {$_ ne 'ALL_YEARS' && $_ ne 'AVERAGE'} @years;
    }

    my @reasons = sort {
        $reasons->{$a}{ALL_YEARS} <=> $reasons->{$b}{ALL_YEARS}
    } grep {real_reason($_)} keys(%$reasons);
    push(@reasons, undef, @COMPUTED);

    my $table = new Text::Table('reason', @years);
    foreach my $reason (@reasons) {
        if (!defined($reason)) {
            $table->add(" ");
        } else {
            $table->add($reason, map {
                $reasons->{$reason}{$_} // '-';
            } @years);
        }
    }

    return $table;
}

# -------------------------------------------------------------------

main();

# -------------------------------------------------------------------

__END__

=head1 AUTHOR

 Conan Yuan

=cut

