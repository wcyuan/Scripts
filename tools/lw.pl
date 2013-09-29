#!/usr/bin/env perl
#

=head1 SYNOPSIS

lw.pl [-v(erbose)] [-csh|-bash] <cmd>*

=cut

# --------------------------------------------------------------------------
# Includes
#

use strict;
use warnings 'all';

use Carp;
use Getopt::Long;
use Pod::Usage;

# --------------------------------------------------------------------------
# Command line options
#

my $SHELL = $ENV{XTERM_SHELL} // $ENV{SHELL};

GetOptions("verbose|v!"  => \my $VERBOSE,
           "shell=s"     => \$SHELL,
           "sh|bash!"    => sub { $SHELL = 'bash' },
           "csh|tcsh!"   => sub { $SHELL = 'tcsh' },
           );

# --------------------------------------------------------------------------
# Functions
#

sub verbose($) {
    my ($str) = @_;
    print "$str\n"
        if $VERBOSE;
}

sub find_perl_module($) {
    my ($file) = @_;
    my $cmd = "perldoc -v $file 3>/dev/null 2>&1 1>&3 | grep '^Found as'";
    verbose("Running: $cmd");
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
    my $cmd = "python -c 'import $file; " .
              "f = $file.__file__; " .
              "print f[:-1] if f.endswith(\".pyc\") else f' 2>/dev/null";
    verbose("Running: $cmd");
    chomp(my $python_module = `$cmd`);
    if ($? == 0 && -f $python_module) {
        return $python_module;
    }
    return $file;
}

# --------------------------------------------------------------------------
# Main
#

my @files = ();
my $less_in = 0;
my $to_less;

foreach my $cmd (@ARGV) {
    # If the command has a / in it, then it's probably the full path
    # already, no need to use where to find it.
    if ($cmd =~ m@/@) {
        push(@files, $cmd);
        next;
    }

    # Different shells could have different paths and different aliases
    my $shell_cmd = "echo type -a $cmd | bash -s -l 2>/dev/null";
    if (defined($SHELL) && $SHELL =~ /csh/) {
        $shell_cmd = "echo where $cmd | tcsh -s";
    }

    my $found = 0;
    verbose("Running: $shell_cmd");
    open(WHERE,"$shell_cmd |")
        or confess("Error running \"$shell_cmd\": $! $? $@");
    while(my $line = <WHERE>) {
        $found = 1;
	chomp($line);

	if (-x $line) {
	    push(@files, $line);
	}
        elsif ($line =~ m/^$cmd is (\/.*)$/) {
	    push(@files, $1);
        }
        else {
            # If the command is an alias, where will tell you what the
            # alias is.  We want to save that message too.
	    if (!$less_in) {
		push(@files, "-");
		$less_in = 1;
	    }
	    $to_less .= $line . "\n";
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
    my $cmd = "less " . join(" ", map ("'$_'", @files));
    if ($less_in) {
	$cmd = ("echo '" . $to_less . "' | " . $cmd);
    }
    exec($cmd);
}
