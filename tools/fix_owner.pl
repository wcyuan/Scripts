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

Change the owner of a file by mv'ing it out of the way, then cp'ing it
back as the new owner.  If the cp back fails, then we'll mv the file
back where it was.

You can change the owner of a file as long as 
 - you can sudo to the new owner of the file
 - the new owner can write to the directory and /tmp
and either:
 - you can sudo to the file's old owner
 - the file's old owner can write to the file, the directory, and to /tmp
or
 - you can write to the file, the directory, and /tmp

If you can sudo to the file's old owner, we'll mv the file out of the
way as the old owner and cp it back as the new owner.

If you can't sudo to the file's old owner, then we'll mv the file away
as yourself and cp it back as the new owner.  In this case, if the new
owner doesn't have write permissions to the directory, we'll be
copying back the file as yourself, so the file's owner will have
changed anyway.

=cut

use strict;
use warnings 'all';
use Getopt::Long;
use File::Basename qw(basename dirname);
use File::Temp qw(tmpnam);
use Pod::Usage;

# ------------------------------------------------------

# Globals - These are set in parse_command_line and never modified again.  
my ($VERBOSE, $DEBUG, $QUIET);

sub main() {
    my ($user, @fns) = parse_command_line();

    my $me = getpwuid($>) || getpwuid($<) || getlogin();
    if (!defined($user)) {
        $user = $me;
    }
    my $sudo_new = ($user eq $me) ? '' : "sudo -u $user";

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

        my $owner_id = get_owner($fn);
        if ($uid eq $owner_id) {
            warning("Skipping $fn, it already has owner $user");
            $success = 0;
            next;
        }
        my $owner = getpwuid($owner_id);
        my $sudo_old = ($owner eq $me || !can_sudo_to($owner)) ? '' : "sudo -u $owner";

        my $temp_file = tmpnam();
        #my $temp_file = new File::Temp(UNLINK => 0,
        #                               DIR => dirname($fn),
        #                               SUFFIX => join('.', '', $scriptname, $pid, basename($fn)));
        if (!run("$sudo_old mv $fn $temp_file")) {
            $success = 0;
            next;
        }

        if (!run("$sudo_new cp $temp_file $fn")) {
            run("$sudo_old mv $temp_file $fn");
            $success = 0;
            next;
        }

        run("$sudo_old rm -f $temp_file"); 
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

    return ($user, @ARGV);
}

sub get_owner($) {
    my ($fn) = @_;
    my ($dev,$ino,$mode,$nlink,$uid,$gid,$rdev,$size,
        $atime,$mtime,$ctime,$blksize,$blocks) = stat($fn);
    return $uid;
}

sub can_sudo_to($) {
    my ($test_userid) = @_;
    my $rc = system("sudo -u $test_userid -S /bin/true </dev/null 2>/dev/null");
    return $rc == 0;
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