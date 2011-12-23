#!/usr/local/bin/perl -w
#
###############################################################################
###
### show me the changes in the last commit of a CVS'ed file
###
use strict;
use Getopt::Std;
use vars qw($opt_r $opt_b $opt_t $opt_l);
use File::Basename qw(dirname basename);

getopts("r:b:tl") or die;

my ($revs_back) = defined($opt_b) ? abs($opt_b) : 1;
my ($revno) = $opt_r;
my ($last_commit_mode) = defined($opt_t);
my $fast = !defined($opt_l);

if ($last_commit_mode) {
    if ($revno || defined($opt_b)) {
	die "Revno (-r) and revs back (-b) meaningless in last commit mode (-t)";
    }
} else {
    if (!$fast) {
	die "slow mode (-l) meaningless except in last commit mode (-t)";
    }
}

use constant RCS => "RCS";
use constant CVS => "CVS";
use constant SVN => "SVN";

sub repository_type($) {
    my ($file) = @_;
    my $dirname = dirname($file);
    my $basename = basename($file);
    my $CVS_ENTRIES = "$dirname/CVS/Entries";
    if (-f $CVS_ENTRIES) {
	return CVS;
    }
    if (-d "$dirname/RCS" || -f "$file,v") {
	return RCS;
    }
    if (-d "$dirname/.svn") {
	return SVN;
    }
    die "Can't figure out repository for file $file";
}

sub last_rev ( $;$ ) {
    my ($file, $checked_out) = @_;
    $checked_out = 1 unless(defined($checked_out));
    my ($rev, $repository_file);
    if ($checked_out) {
	my $dirname = dirname($file);
	my $basename = basename($file);
        if (repository_type($file) eq RCS) {
            chomp($rev = `rlog -h $file | grep head | cut -d' ' -f 2-`);
        } elsif (repository_type($file) eq CVS) {
            my $CVS_ENTRIES = "$dirname/CVS/Entries";
            unless(open(CVS_ENTRIES, $CVS_ENTRIES)) {
                warn "Can't find CVS Entries file: $CVS_ENTRIES, $!";
                return;
            }
            while(<CVS_ENTRIES>) {
                my (undef, $filename, $revision, $date, $other) = split '/';
                if (defined($filename) && $filename eq $basename) {
                    $rev = $revision;
                    last;
                }
            }
            unless(close(CVS_ENTRIES)) {
                warn "Can't close $CVS_ENTRIES";
                return;
            }
        }
    } else {
        if (repository_type($file) eq CVS) {
            my $status_cmd = "cvs -Q status -l $file |";
            unless(open(STATUS, $status_cmd)) {
                warn "Can't run $status_cmd, $! $?";
                return;
            }
            while(<STATUS>) {
                next unless ($_ =~ /^\s*Repository revision:\s*(.*?)\s*$/);
                my $rev_info = $1;
                next if ($rev_info =~ /No revision control file/);
                ($rev, $repository_file) = split(' ', $rev_info, 2);
            }
            unless(close(STATUS)) {
                warn "Can't close $status_cmd: $? $!";
                return;
            }
        }
    }
    # rev is not necessarily defined
    # it won't be defined if the file doesn't exist or isn't cvs'ed
    # because cvs status will still exist successfully
    return $rev;
}


# given a file under svn control, return the svn revisions where that
# file changed.
sub svn_revision_list ( $;$ ) {
    my ($file, $revs_needed) = @_;
    my $cmd = "svn log -q $file 2>&1";
    my $error = 0;
    open(SVNLOG, "$cmd |")
	or ($error = 1);
    if ($error) {
	warn("Error running $cmd: $? $@ $!");
	return;
    }
    my @revs;
    while(my $line = <SVNLOG>) {
	next if ($line =~ m/^-*$/);
	# rely on the fact that the revision is the first column
	my ($rev) = split(' ', $line);

	$rev =~ s/^r//;
	push(@revs, $rev);

	if (defined($revs_needed) && scalar(@revs) > $revs_needed) {
	    last;
	}
    }
    close(SVNLOG);
    return \@revs;
}

FILE:
foreach my $file (@ARGV) {
    if ($last_commit_mode) {
	if (repository_type($file) ne CVS) {
	    die("Can only use last_commit_mode on a CVS repository");
	}
	my ($rev, $repository_file, $log_cmd);
	if ($fast) {
	    $log_cmd = "cvs log $file 2>/dev/null |";
	} else {
	    $rev = last_rev($file, 0);
	    if (!defined($rev)) {
		warn "skipping $file";
		next FILE;
	    }
	    $log_cmd = "cvs log -r$rev $file 2>/dev/null |";
	}
	unless(open(LOG, $log_cmd)) {
	    warn "Can't run $log_cmd, $! $?";
	    next;
	}
      LOG:
	while(<LOG>) {
	    if ($fast) {
		if ($_ =~ /^\s*revision\s*([^\s]*)\s*$/) {
		    $rev = $1;
		}
	    }
	    next unless /^\s*date:/;
	    chomp;
	    if (!defined($rev)) {
		warn "$file: no rev before date: $_";
		next LOG;
	    }
	    my (@info) = split(/;  /, $_);
	    my $date;
	    foreach my $data (@info) {
		my ($var, $val) = split(/: /, $data);
		if ($var eq "state") {
		    next LOG unless ($val eq "Exp");
		}
		elsif ($var eq "date") {
		    $date = $val;
		} 
	    }
	    $date =~ s@/@@g;
	    next LOG unless (defined($date));
	    print "$date $file $rev $_\n";
	    last LOG if ($fast);
	}
	unless(close(LOG)) {
	    # this can happen if we just close the pipe before it 
	    # is done running.  we ignore the error since we just 
	    # want to close the pipe anyway.  
	    # warn "Can't close $log_cmd: $? $!";
	    next;
	}
    } else {
	if (repository_type($file) eq SVN) {
	    my $prev;
	    if ($revs_back != 1) {
		my $rev_list = svn_revision_list($file, $revs_back);
		if (defined($rev_list)) {
		    if (scalar(@$rev_list) >= $revs_back) {
			if (defined($revno)) {
			    warn("specified both revs_back and revno -- ignoring revno $revno");
			}
			$revno = $rev_list->[$revs_back-1];
		    } else {
			die "Not enough revisions: $revs_back, " . scalar(@$rev_list);
		    }
		}
	    }
	    if (defined($revno)) {
		$prev = $revno - 1;
	    } else {
		$prev = "PREV";
		$revno = "COMMITTED";
	    }
	    system "svn log -r$prev:$revno $file";
	    system "svn diff -r$prev:$revno $file";
        } elsif (repository_type($file) eq CVS ||
                 repository_type($file) eq RCS) {
	    my $last_revision;
	    if (defined($revno)) {
		$last_revision = $revno;
	    } else {
		$last_revision = last_rev($file)
	    }
	    if (!defined $last_revision) {
		warn "skipping $file";
		next FILE;
	    }
	    my @rev_nos = split(/\./, $last_revision);
	    $rev_nos[$#rev_nos] -= $revs_back;
	    die "Not enough revisions: $last_revision" if ($rev_nos[$#rev_nos] < 1);
	    my $prev_revision = join(".", @rev_nos);
	    if ($revs_back > 1) {
		$rev_nos[$#rev_nos]++;
		$last_revision = join(".", @rev_nos);
	    }
	
            if (repository_type($file) eq RCS) {
                system "rlog -r$last_revision $file";
                system "rcsdiff -u -r$prev_revision -r$last_revision $file";
            } else {
                system "cvs log -r$last_revision $file";
                system "cvs diff -u -r $prev_revision -r $last_revision $file";
            }
	}
    }
}
 
