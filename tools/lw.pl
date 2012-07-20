#!/usr/local/bin/perl -w
#
###############################################################################
###
### $Id: lw.pl,v 1.3 2011/12/29 15:49:16 yuanc Exp $
### $Source: /u/yuanc/testbed/perl/RCS/lw.pl,v $
###
use strict;
use English;
use Getopt::Std;
our($opt_n);
getopts("n:") or die;
my ($n) = abs($opt_n) if defined($opt_n);

my @files = ();
my $less_in = 0;
my $to_less;

sub find_perl_module($) {
    my ($file) = @_;
    my $cmd = "desperldoc -v $file 3>/dev/null 2>&1 1>&3 | grep '^Found as'";
    chomp(my $perldoc_output = `$cmd`);
    if ($? == 0 && $perldoc_output !~ m/^\s*$/) {
        my $perl_module = (split ' ', $perldoc_output, 3)[2];
        if (!defined($perl_module) || $perl_module =~ m/^\s*$/) {
        } else {
            return $perl_module;
        }
    }
    return $file;
}

sub find_python_module($) {
    my ($file) = @_;
    my $cmd = "despydoc --where $file 2>/dev/null";
    chomp(my $python_module = `$cmd`);
    if ($? == 0) {
        return $python_module;
    }
    return $file;
}

foreach my $cmd (@ARGV) {
    # If the command has a / in it, then it's probably the full path
    # already, no need to use where to find it.
    if ($cmd =~ m@/@) {
        push(@files, $cmd);
        next;
    }
    my $found = 0;
    open(WHERE,"echo where $cmd | tcsh -s |") or warn "$cmd: $! $?";
    while(<WHERE>) {
	next if (defined($n) && $INPUT_LINE_NUMBER != $n);
        $found = 1;
	chomp;
	if (-x $_) {
	    push(@files, $_);
	} else {
            # If the command is an alias, where will tell you what the
            # alias is.  We want to save that message too.
	    if (!$less_in) {
		push(@files, "-");
		$less_in = 1;
	    }
	    $to_less .= $_ . '\n';
	}
    }
    close(WHERE);

    if (!$found) {
        if ($cmd =~ /::/) {
            my $pm = find_perl_module($cmd);
            if (defined($pm)) {
                push(@files, $pm);
            }
        } else {
            my $py = find_python_module($cmd);
            if (defined($py)) {
                push(@files, $py);
            }
        }
    }
}

if (scalar(@files) > 0) {
    my $cmd = "less " . join(" ", @files);
    if ($less_in) {
	$cmd = ("echo '" . $to_less . "' | " . $cmd);
    }
    exec($cmd);
}
