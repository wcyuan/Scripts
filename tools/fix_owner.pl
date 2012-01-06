#!/usr/local/bin/perl -w

=head1 NAME

fix_owner.pl - Change the owner of a file using sudo, mv, and cp

=head1 SYNOPSIS

  fix_owner.pl [options] <file>*

  Options: 
    --quiet             Suppress messages about missing files or 
                        if the file already has the right owner
    --verbose           Print the commands being run.  Overrides quiet.  
    --debug             Print the command that would be run without running them
    --user              The user to set the owner to


=head1 DESCRIPTION

Change the owner of a file.

You can change the owner of a file as long as 
 - you can write to the file
 - you can write to the directory
 - you can sudo to the new owner.  
 - the new owner can write to the directory
 - both you and the new owner can write to the /tmp directory

=cut

use strict;
use warnings 'all';
use Getopt::Long;
use File::Basename qw(basename);
use File::Temp qw(tmpnam);
use Pod::Usage;

# ------------------------------------------------------

# Globals - These are set in parse_command_line and never modified again.  
my ($VERBOSE, $DEBUG, $QUIET);

sub main() {
    my ($user, @fns) = parse_command_line();

    my $uid = getpwnam($user);
    my $scriptname = basename($0);
    my $pid = $$;

    my $success = 1;

    foreach my $fn (@fns) {
        if (! -f $fn) {
            warning("Can't find $fn, skipping");
            $success = 0;
            next;
        }

        if (! -f $fn || $uid eq owner($fn)) {
            warning("Skipping $fn, it already has owner $user");
            $success = 0;
            next;
        }

        my $temp_file = new File::Temp(UNLINK => 0,
                                       SUFFIX => join('.', '', $scriptname, $pid, basename($fn)));

        if (!run("mv $fn $temp_file")) {
            $success = 0;
            next;
        }

        if (!run("sudo -u $user cp $temp_file $fn")) {
            run("mv $temp_file $fn");
            $success = 0;
            next;
        }

        run("rm -f $temp_file"); 
    }

    if (!$success) {
        exit 1;
    }
}

# ------------------------------------------------------

sub parse_command_line() {
    GetOptions("debug|d!"   => \$DEBUG,
               "user|u=s"   => \my $user,
               "verbose|v!" => \$VERBOSE,
               "quiet"      => \$QUIET)
        or pod2usage();

    if (!defined($user)) {
        $user = getlogin() || getpwuid($<);
    }
    return ($user, @ARGV);
}

sub owner($) {
    my ($fn) = @_;
    my ($dev,$ino,$mode,$nlink,$uid,$gid,$rdev,$size,
        $atime,$mtime,$ctime,$blksize,$blocks) = stat($fn);
    return $uid;
}

sub run_cmd($;$$$$$) {
    my ($cmd, $retval_ref, $die_on_error, $verbose, $debug, $quiet) = @_;
    $die_on_error = defined($die_on_error) ? $die_on_error : 0;
    $verbose      = defined($verbose)      ? $verbose      : 0;
    $debug        = defined($debug)        ? $debug        : 0;
    my $success;
    my $retval = "";
    if ($debug) {
        if (!$quiet || $verbose) {
            print "Would run: $cmd\n";
        }
	$success = 1;
    } else {
	if ($verbose) {
	    print "Running: $cmd\n";
	} 
	chomp($retval = `$cmd`);
	if ($?) {
	    my $error = "Error running \"$cmd\": $? $retval";
	    if ($die_on_error) {
		die $error;
	    } else {
		warn $error;
	    }
	    $success = 0;
	} else {
	    $success = 1;
	}
	if (defined($retval_ref) && ref($retval_ref) eq "SCALAR") {
	    $$retval_ref = $retval;
	}
    }
    return $success;
}

sub warning($) {
    my ($msg) = @_;
    if (!$QUIET || $VERBOSE) {
        warn($msg);
    }
}

sub run($) {
    my ($cmd) = @_;
    return run_cmd($cmd, undef, 0, $VERBOSE, $DEBUG, $QUIET);
}

# ------------------------------------------------------

main();

# ------------------------------------------------------
