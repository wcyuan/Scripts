#!/usr/local/bin/perl -w
#
# recent_largefiles.pl
#

=head1 NAME

recent_largefiles.pl - find recent large files, in a dated directory structure

=head1 SYNOPSIS

  recent_largefiles.pl [options] <dir>

  Options:
    --days_back       days back to search
    --size            min size of files to find (in MB)
    --date            the current date
    --help, -?        shows brief help message
    --perldoc         shows full documentation

=head1 ARGUMENTS

=over

=item I<dir>

The path to search in

=back

=head1 OPTIONS

=over 4

=item I<--days_back>

Search for files that were modified within the last
these many days

=item I<--size>

The size (in MB) of the files to look for

=item I<--date>

The current date

=item I<--help>

Print a brief help message and exit.

=item I<--perldoc>

Print the perldoc page and exit.

=back

=head1 DESCRIPTION

Looks for large, recently modified files within a dated directory
structure.

The goal of this script is to look for files that may have been
recently generated that are consuming lots of disk.  It requires that
the directory structure has yyyy/mm/dd in it somewhere, and uses that
date to prune the search space.  If you just do a find for recently
changed files, you still have to look at every file, which is slow.

=cut

use strict;
use warnings 'all';
use Pod::Usage;

use File::Find;
use File::Basename qw(basename dirname);
use File::stat;

use Date::Calc qw(Add_Delta_Days check_date);
use Getopt::Long;
use Log::Log4perl qw(:levels);
use Carp;

# Provide stack traces
$SIG{__WARN__} = \&Carp::cluck;
$SIG{__DIE__} = \&Carp::confess;

# ----------------------

Log::Log4perl->easy_init($ERROR);
my $LOGGER = Log::Log4perl->get_logger();

# ----------------------

sub main() {
    my ($end, $days_back, $size, $follow, @dirs) = parse_command_line();

    my $start = add_days($end,  -$days_back);
    find({ wanted => sub { return wanted($start, $end, $size) },
           follow => $follow },
         @dirs);
}

# ----------------------

sub parse_command_line() {

    # Default values
    my $days_back = 10;
    my $size = 100;

    # Normally, do not follow because we just want to know what's
    # taking up space on a given partition, so if a link goes to
    # another partition, we don't care about it.  And if a link goes
    # somewhere on this partition, we should find it some other way.
    my $follow = 0;

    # Parse any command-line options
    GetOptions( "days_back=i"  => \$days_back,
                "size=i"       => \$size,
                "date=i"       => \my $date,
                "verbose"      => sub { $LOGGER->level($DEBUG) },
            )
        or pos2usage();

    if (!defined($date)) {
        $date = localtime_to_yyyymmdd();
    }

    # Parse any script arguments
    my @dirs = @ARGV;

    return ($date, $days_back, $size, $follow, @dirs);
}

# ----------------------
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

sub get_yyyymm($) {
    my ($yyyymmdd) = @_;
    my $yyyymm = substr($yyyymmdd, 0, -2);
    return $yyyymm;
}

###
# Functions using Date::Calc dates, or converting to/from yyyymmdd and
# Date::Calc dates
##
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

sub add_days($$) {
    my ($from, $to_add) = @_;
    my ($from_year, $from_month, $from_day) = from_yyyymmdd($from);
    ($from_year, $from_month, $from_day) =
        Add_Delta_Days($from_year, $from_month, $from_day, $to_add);
    return to_yyyymmdd($from_year, $from_month, $from_day);
}

sub valid_date($) {
    my ($date) = @_;
    if (length($date) < 8) {
        return undef;
    }
    if ($date !~ m/^\d+$/) {
        return undef;
    }
    my ($year, $month, $day) = from_yyyymmdd($date);
    return check_date($year, $month, $day);
}

###
# Functions for getting the current date
###
sub adjlocaltime {
    my @data = scalar(@_) > 0 ? localtime($_[0]) : localtime();
    my ($sec, $min, $hour, $mday, $mon, $year, $wday, $yday, $isdst) = @data;
    $year += 1900;
    $mon++;
    return ($sec, $min, $hour, $mday, $mon, $year, $wday, $yday, $isdst);
}

sub localtime_to_yyyymmdd {
    my @data = scalar(@_) > 0 ? adjlocaltime($_[0]) : adjlocaltime();
    my ($sec, $min, $hour, $mday, $mon, $year, $wday, $yday, $isdst) = @data;
    return to_yyyymmdd($year, $mon, $mday);
}

# ----------------------

sub looks_like_year($$) {
    my ($file, $dir) = @_;
    if ($file =~ m/^\d{4}$/ && $file > 1900) {
        return $file;
    }
    return undef;
}

sub looks_like_month($$) {
    my ($file, $dir) = @_;
    if ($file =~ m/^\d{2}$/ && $file < 13) {
        my $year = looks_like_year(basename($dir), dirname($dir));
        if (defined($year)) {
            return $year . $file;
        }
    }
    return undef;
}

sub looks_like_day($$) {
    my ($file, $dir) = @_;
    if ($file =~ m/^\d{2}$/ && $file < 32) {
        my ($yearmonth) = looks_like_month(basename($dir), dirname($dir));
        if (defined($yearmonth)) {
            return $yearmonth . $file;
        }
    }

    if (valid_date($file)) {
        return $file;
    } else {
        return undef;
    }
}

sub wanted($$$) {
    my ($start_date, $end_date, $size) = @_;

    my $file = $_;
    my $dir  = $File::Find::dir;
    my $name = $File::Find::name;
    if (-d $file) {
        my $date = looks_like_year($file, $dir);
        if (defined($date)) {
            if ($date < get_year($start_date) ||
                $date > get_year($end_date))
            {
                $LOGGER->debug("Pruning $name, year $date not in " .
                               "($start_date, $end_date)");
                $File::Find::prune = 1;
            }
            return;
        }

        $date = looks_like_month($file, $dir);
        if (defined($date)) {
            if ($date < get_yyyymm($start_date) ||
                $date > get_yyyymm($end_date))
            {
                $LOGGER->debug("Pruning $name, month $date not in " .
                               "($start_date, $end_date)");
                $File::Find::prune = 1;
            }
            return;
        }

        $date = looks_like_day($file, $dir);
        if (defined($date)) {
            if ($date < $start_date ||
                $date > $end_date)
            {
                $LOGGER->debug("Pruning $name, day $date not in " .
                               "($start_date, $end_date)");
                $File::Find::prune = 1;
            }
            return;
        }
    } elsif (-f $file) {
        my $sb = lstat($file);
        # convert size to Mb
        my $fsize = sprintf '%.1f', $sb->size() / 1_000_000;
        if ($fsize < $size) {
            $LOGGER->debug("Skipping $name, size $fsize < $size");
            return;
        }
        my $date = localtime_to_yyyymmdd($sb->mtime);
        if ($date < $start_date || $date > $end_date) {
            $LOGGER->debug("Skipping $name, modified date $date not in " .
                           "($start_date, $end_date)");
            return;
        }

        print join(' ',
                   $fsize,
                   $date,
                   $File::Find::name,
                  ) . "\n";
    }
}

# ----------------------

main();

# ----------------------

__END__

=head1 AUTHOR

 Conan Yuan

=cut

