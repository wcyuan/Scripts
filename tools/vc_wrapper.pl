#!/usr/bin/env perl
#
# vc_wrapper.pl
# @desc:  wrapper around cvs and svn
#
# Conan Yuan, 20090220
#

=head1 NAME

vc_wrapper.pl - wrapper around cvs and svn

=head1 SYNOPSIS

  vc_wrapper.pl [options] 

  Options: 
    --help, -?        shows brief help message
    --perldoc         shows full documentation

  See also Getopt::Long for complete standard options list.

=head1 ARGUMENTS

=over

=item I<switchrel>

change a file from the trunk version to the latest release version
only prints the command to run, unless -run is specified.  

=item I<switchtrunk>

change a file from the latest release version to the trunk version
only prints the command to run, unless -run is specified.  

=item I<uptrunk>

merge the last changes made to the trunk into the release version
only prints the command to run, unless -run is specified.  

=item I<rmsg>

print the commit message that should be used when commiting to the
release branch.  The message will take the commit message from the
trunk and add to it a line pointing to the trunk revision.  

=item I<fdiff> and I<fmerge>

Aka foreign_diff and foreign_merge.  

Let's say you made some changes to file foo that you didn't check in.
Then you want to make an unrelated change to foo that you do want to
check in, but you don't want to lose the changes that you already have
and you don't want to check them in.  So you move foo to foo.save,
update foo, edit it, and check it in.  Later, you release that
foo.save is still there, and has changes based on an old version.  If
you wanted to update foo.save to the latest version, you'd want to
update foo to the old version, replace it with foo.save, then update
it to the latest version.  That's what foreign_merge does.  If you
just want to see what changes foo.save contains, you can do
foreign_diff and it will diff foo.save against the old version of foo.
Both of the commands work by looking for the $Id$ tags in the file, so
if that tag doesn't exist, this command won't work.

=back

=head1 OPTIONS

=over 4

=item I<--verbose>

print out all the commands being run and other debugging information

=item I<--run>

for uptrunk, switchrel, and switchtrunk, not only print the command, but run it.  

=item I<--help>

Print a brief help message and exit.

=item I<--perldoc>

Print the perldoc page and exit.

=back

=head1 DESCRIPTION

 1. if you use svn instead of cvs, or vice versa, this corrects it

 2. if you use svn diff -u, this corrects it by removing the -u

 3. if you use cvs diff, this corrects it by adding a -u

anytime it makes a change, it issues a warning

Also adds some special commands:

 svn switchrel [file]
   - change a file from the trunk version to the latest release version

 svn switchtrunk [file]
   - change a file from the latest release version to the trunk version

 svn uptrunk [file]
   - merge the last changes made to the trunk into the release version

 svn rmsg [file]
   - pring the commit message to use when pushing a trunk revision to the release branch

These commands just print the commands you need to run to do all of
these things, they don't actually run those commands.  Unless you say
"-run" as well.

 svn foreign_diff <file>*
 svn foreign_merge <file>*

Let's say you made some changes to file foo that you didn't check in.
Then you want to make an unrelated change to foo that you do want to
check in, but you don't want to lose the changes that you already have
and you don't want to check them in.  So you move foo to foo.save,
update foo, edit it, and check it in.  Later, you release that
foo.save is still there, and has changes based on an old version.  If
you wanted to update foo.save to the latest version, you'd want to
update foo to the old version, replace it with foo.save, then update
it to the latest version.  That's what foreign_merge does.  If you
just want to see what changes foo.save contains, you can do
foreign_diff and it will diff foo.save against the old version of foo.
Both of the commands work by looking for the $Id$ tags in the file, so
if that tag doesn't exist, this command won't work.

fdiff and fmerge work for both SVN and CVS

=cut

# ------------------------------------------------------------------------------

package Logger;

use Carp;
use Data::Dumper;

our %LEVELS = (DEBUG      => 50,
	       INFO       => 40,
	       WARN       => 30,
	       ERROR      => 20,
	       LOGCONFESS => 10);
our %REVLEVELS = map { $LEVELS{$_} => $_ } keys(%LEVELS);

sub new($;$) {
  my ($this, $level) = @_;
  my $class = ref($this) || $this;
  my $self = {};
  $level //= 'WARN';
  bless $self, $class;
  return $self;
}

sub level($;$) {
  my ($self, $level) = @_;
  if (defined($level)) {
    if (defined($LEVELS{$level})) {
      $self->{level} = $level;
    } elsif (defined($REVLEVELS{$level})) {
      $self->{level} = $REVLEVELS{$level};
    } else {
      confess("Unknown level: $level");
    }
  }
  return $self->{level};
}

sub output($$$) {
  my ($self, $level, $msg) = @_;
  if ($LEVELS{$self->{level}} >= $LEVELS{$level}) {
    my ($pack, $fn, $line, $sub) = caller(2);
    my $str = "[$level][$sub:$line] $msg";
    if ($level eq 'LOGCONFESS') {
      confess($str);
    } else {
      print STDERR "$str\n";
    }
  }
}

sub debug($$)      { $_[0]->output('DEBUG',      $_[1]) }
sub info($$)       { $_[0]->output('INFO',       $_[1]) }
sub warn($$)       { $_[0]->output('WARN',       $_[1]) }
sub error($$)      { $_[0]->output('ERROR',      $_[1]) }
sub logconfess($$) { $_[0]->output('LOGCONFESS', $_[1]) }

# ------------------------------------------------------------------------------
# Imports
#

package main;

use strict;
use warnings 'all';
use Pod::Usage;
use File::Basename qw(basename dirname);
use Data::Dumper qw(Dumper);
use File::Compare qw(compare);
use Cwd qw(abs_path);
# should probably use File::Spec

use Getopt::Long qw(GetOptions);
#use Log::Log4perl qw(:levels);

# ------------------------------------------------------------------------------
# Global Variables
#

my $NO_WRITE;
#Log::Log4perl->easy_init($WARN);
#my $LOGGER = Log::Log4perl->get_logger();
my $LOGGER = new Logger();

#
# We want to run svn and cvs, but we've already wrapped svn and cvs in
# this script, so we have to make sure that when we call svn or cvs,
# we're calling the real ones, not this script.
#
# We also don't want to hard-code the location of svn and cvs since
# they could be in different locations on linux.
#
sub find_next_cmd($) {
    my ($root) = @_;
    my @path = split(':', $ENV{PATH});
    foreach my $dir (@path) {
        my $file = "$dir/$root";
        if (-x $file && compare($file, $0) != 0) {
            # just to be paranoid -- we really don't want to start a
            # recursive loop
            if ($file =~ m/yuanc/) {
                $LOGGER->error("Skipping $file in yuanc's directory");
                next;
            }
            return $file;
        }
    }
    $LOGGER->logconfess("No other $root found in $ENV{PATH}\n");
}

my $SVN = find_next_cmd('svn');
my $CVS = find_next_cmd('cvs');
my $GIT = find_next_cmd('git');
my $RCS = find_next_cmd('rcs');
my $DIFF = 'diff';
my %CMDS = ("svn" => $SVN,
	    "cvs" => $CVS,
	    "git" => $GIT,
	    "rcs" => $RCS);

# ------------------------------------------------------------------------------

sub main() {
    my (# the command that was passed in:
        $cmd_name, 
        $cmd_options,
        $action,
        $subcmd_options,
        $files,

        # options for our general behavior:
        $run_cmds,

        # options for modifying standard subcommands:
        $diff_arg_u,
        $diff_arg_w,
        $ann_arg_v,
        $up_arg_d,
        $up_arg_P,

        # options for our added subcommands:
        $foreign_arg_repos,
        $foreign_arg_fn,
        $foreign_arg_version,
        $uptrunk_arg_revision,
        $lastrev_arg_revno,
        $lastrev_arg_revs_back,
        $grep_hist_arg_missing,
        $grep_hist_arg_first_occur,
        $grep_hist_arg_last_occur,
       ) = parse_command_line();

    my $repo_type = get_repo_type($cmd_name, $action, $files);

    customize_subcmd_options($repo_type, $action, $subcmd_options,
                             $diff_arg_u, $diff_arg_w, 
                             $ann_arg_v, 
                             $up_arg_d, $up_arg_P);

    if (defined($action)) {
        if ($action eq "switch_to_release" ||
            $action eq "switchrel" ||
            $action eq "switchrelease") {

            switch_to_release($repo_type, $action, $files, $run_cmds);
            return;

        } elsif ($action eq "switch_to_trunk" ||
                 $action eq "switchtrunk") {

            switch_to_trunk($repo_type, $action, $files, $run_cmds);
            return;

        } elsif ($action eq "update_from_trunk" || 
                 $action eq "uptrunk") {

            update_from_trunk($repo_type, $action, $files, $run_cmds, $uptrunk_arg_revision);
            return;

        } elsif ($action eq "release_message" || 
                 $action eq "rmsg") {

            release_message($repo_type, $action, $files);
            return;

        } elsif ($action eq "foreign_diff" || 
                 $action eq "fdiff") {

            foreign_diff($repo_type, $action, $files,
                         $foreign_arg_repos,
                         $foreign_arg_fn,
                         $foreign_arg_version);
            return;

        } elsif ($action eq "foreign_merge" || 
                 $action eq "fmerge") {

            foreign_merge($repo_type, $action, $files);
            return;
        } elsif ($action eq "lastrev" || $action eq 'rlastrev') {
            
            lastrev($repo_type, $action, $cmd_options, $files, $lastrev_arg_revs_back, $lastrev_arg_revno);
            return;
        } elsif ($action eq "grep-hist") {
            
            grep_hist($repo_type, $action, $subcmd_options, $files, 
                      $grep_hist_arg_missing, 
                      $grep_hist_arg_first_occur,
                      $grep_hist_arg_last_occur);
            return;
        } elsif ($action eq "bisect-all") {
            
            bisect_all($repo_type, $action, $subcmd_options, $files);
            return;
        }
    }

    run_modified_command($repo_type, $cmd_options, $action, $subcmd_options, $files,
                         $diff_arg_u, $diff_arg_w, 
                         $ann_arg_v, 
                         $up_arg_d, $up_arg_P);
}


# ------------------------------------------------------------------------------
# COMMAND LINE and DEFAULTS
#

# This function takes as input a reference to an array of arguments.
# It separates the arguments into leading options and regular args.
# Options are anything that starts with '-' (even '--').  Leading
# options are all the options that appear before any non-option.
# This changes the input array in place.  
#
# We are trying to do this without knowing what the actual options are
# and what they mean.  If there is an option that takes an argument,
# this won't work because we'll think the argument to the option is
# the first non-option.  So if we've got "-r foo -d", then we'll
# recognize -r as an option, but we'll think the rest of the arguments
# are "foo -d", when in fact all of those should be considered
# options.
sub consume_leading_options($) {
    my ($a) = @_;
    my @leading_options;
    while (scalar(@$a) > 0 && $a->[0] =~ m/^-/) {
        push(@leading_options, shift(@$a));
    }
    return @leading_options;
}

# modifies ARGV in place
sub parse_command_line() {

    # Parse any general options
    # Since we want to parse the command's options separately from the
    # sub-command's arguments, use "require order" so that as soon as it
    # sees a non-option, it treats everything else as an argument.  
    #
    # use pass_through, since we want basic options, but other options
    # should just be passed through.
    Getopt::Long::Configure("pass_through", "require_order", "noauto_abbrev", 
                            "noignore_case");
    GetOptions( "run" => \my $run_cmds,
                "no_write" => \$NO_WRITE,
                "verbose|v" => sub { $LOGGER->level('DEBUG') },
              )
        or pod2usage();

    my $orig_cmd_line = join(' ', $0, @ARGV);
    $LOGGER->debug("Running $orig_cmd_line");

    # Save the original arguments
    my $cmd_name = basename($0);
    my @cmd_options = consume_leading_options(\@ARGV);
    $LOGGER->debug("cmd_options = '" . join(', ', @cmd_options) . "'");

    # Parse any command options
    my $action;
    my $diff_arg_u;
    my $diff_arg_w;
    my $ann_arg_v;
    my $up_arg_d;
    my $up_arg_P;
    my $foreign_arg_repos;
    my $foreign_arg_fn;
    my $foreign_arg_version;
    my $uptrunk_arg_revision;
    my $lastrev_arg_revno;
    my $lastrev_arg_revs_back;
    my $grep_hist_arg_missing;
    my $grep_hist_arg_first_occur;
    my $grep_hist_arg_last_occur;
    if (scalar(@ARGV) > 0) {
        $action = shift(@ARGV);

        $LOGGER->debug("Action = $action");

        if ($action eq "fdiff" || 
            $action eq "foreign_diff" || 
            $action eq "foreign_merge" || 
            $action eq "fmerge") 
        {
            Getopt::Long::Configure("no_pass_through");
            GetOptions( "repository|r=s" => \$foreign_arg_repos,
                        "file|fn|filename|f=s" => \$foreign_arg_fn,
                        "version|v=s" => \$foreign_arg_version,
                      )
                or pod2usage();
        } elsif ($action eq "uptrunk") {
            Getopt::Long::Configure("no_pass_through");
            GetOptions( "revision|r=i" => \$uptrunk_arg_revision,
                      )
                or pod2usage();
        } elsif ($action eq "lastrev" || $action eq 'rlastrev') {
            Getopt::Long::Configure("no_pass_through", "bundling");
            GetOptions( "revno|r=s" => \$lastrev_arg_revno,
                        "revs_back|b=i" => \$lastrev_arg_revs_back,
                      )
                or pod2usage();
        } elsif ($action eq "grep-hist") {
            Getopt::Long::Configure("no_pass_through");
            GetOptions( "missing" => \$grep_hist_arg_missing,
                        "first"   => \$grep_hist_arg_first_occur,
                        "last"    => \$grep_hist_arg_last_occur,
                      )
                or pod2usage();
        } else {
            # use pass_through since we want some special handling of
            # certain options (like -u), and all other options should
            # just be passed through.
            Getopt::Long::Configure("pass_through");
            GetOptions( "u" => \$diff_arg_u,
                        "w" => \$diff_arg_w,
                        "v" => \$ann_arg_v,
                        "d" => \$up_arg_d,
                        "P" => \$up_arg_P,
                      )
                or pod2usage();
        }
    }
    my @subcmd_options = consume_leading_options(\@ARGV);
    my @files = @ARGV;
    $LOGGER->debug("subcmd_options = '" . join(', ', @subcmd_options) . "'");
    $LOGGER->debug("files = '" . join(', ', @files) . "'");

    return ($cmd_name, 
            \@cmd_options,
            $action,
            \@subcmd_options,
            \@files,
            $run_cmds,
            $diff_arg_u,
            $diff_arg_w,
            $ann_arg_v,
            $up_arg_d,
            $up_arg_P,
            $foreign_arg_repos,
            $foreign_arg_fn,
            $foreign_arg_version,
            $uptrunk_arg_revision,
            $lastrev_arg_revno,
            $lastrev_arg_revs_back,
            $grep_hist_arg_missing,
            $grep_hist_arg_first_occur,
            $grep_hist_arg_last_occur,
           );
}

# ------------------------------------------------------------------------------
# SVN or CVS?
#
# All the files have to be either SVN or CVS.  We can't handle a mix
# of files from SVN and from CVS.
#

sub my_dirname($) {
    my ($file_or_dir) = @_;

    # Don't check -d on $file_or_dir if it has a new line.  This can
    # happen from refresh_auth_file.py, where it runs "cvs -Q update
    # -m $log_message" and $log_message has a newline.  If you run -d
    # on a string with a newline, you get this warning:
    #
    # Unsuccessful stat on filename containing newline at /u/yuanc/bin/cvs line 228.
    #
    # It's otherwise harmless, though.  
    if ($file_or_dir !~ m/\n/ && -d $file_or_dir) {
	return $file_or_dir;
    } else {
	return dirname($file_or_dir);
    }
}

sub get_git_top($) {
    my ($file) = @_;
    
    my $dirname = my_dirname($file);
    for (my $ii = 0; -d $dirname && $ii < 100; $dirname .= "/..", $ii++) {
        if (-d "$dirname/.git") {
            return $dirname;
        }
    }
    return undef;
}

sub get_repo_type($$$) {
    my ($cmd_name, $action, $files) = @_;
    if (defined($action) && 
        ($action eq "co" || $action eq "checkout")) {
        # nop

        # if we are checking out a repository, then this function
        # doesn't work, since it looks for an existing .svn/CVS/.git
        # directory that won't exist yet.  So, for checkouts, assume
        # that the user knows which of svn/cvs/etc to use.
    } else {
        my $file_to_check;
        # Check the first argument that is actually a file.  If none
        # of the arguments are existing files, then default to the
        # last file, not the first.  Check the last file, not the
        # first file.  Since the files are just the remaining
        # arguments that we couldn't parse, it could include switches
        # for the svn statement (like -r).  So the first few "files"
        # might not actually be files.
        #
        # Make sure we can handle things like:
        # svn info svn+ssh://invest2.nyc/proj/infra/svn/repository/base/branches/rel_20120316
        # svn info --xml svn+ssh://invest2.nyc/proj/infra/svn/repository/base/branches/rel_20120316
        # svn info <directory>
        foreach my $file (@$files) {
            # Don't check -e on $file if it has a new line.  Same
            # reason as in my_dirname (see the comment there).
            if ($file !~ m/\n/ && -e $file) {
                $file_to_check = $file;
                last;
            }
        }
        if (!defined($file_to_check)) {
            if (scalar(@$files) > 0) {
                $file_to_check = $files->[$#$files];
            } else {
                $file_to_check = '.';
            }
        }

        $LOGGER->debug("Checking vc for $file_to_check");
        my $dirname = my_dirname($file_to_check);
        my $new_cmd_name;
        if (-d "$dirname/.svn") {
            $new_cmd_name = "svn";
        } elsif ($file_to_check =~ m@^svn\+ssh://@) {
            $new_cmd_name = "svn";
        } elsif (-f "$dirname/CVS/Entries") {
            $new_cmd_name = "cvs";
        } elsif (-d "$dirname/RCS") {
            $new_cmd_name = "rcs";
        } elsif (defined(get_git_top($file_to_check))) {
            $new_cmd_name = "git";
        } else {
            $LOGGER->warn("Couldn't find repo for $file_to_check ($dirname)");
        }
        if (defined($new_cmd_name)) {
            if ($cmd_name ne $new_cmd_name) {
                $LOGGER->warn("Using $new_cmd_name instead of $cmd_name");
            }
            $cmd_name = $new_cmd_name;
        }
    }
    return $cmd_name;
}

# ------------------------------------------------------------------------------
# Run
#

sub run ( $;$ ) {
    my ($cmd, $options) = @_;
    my ($always, $panic_on_error, $no_warn_on_error, $exec);
    if (defined($options)) {
	if (ref($options) ne 'HASH') {
	    $LOGGER->logconfess('Usage: run($cmd, \%options)');
	}
	foreach my $key (keys %$options) {
	    if ($key =~ m/^always$/io && $options->{$key}) {
		$always = 1;
	    } elsif ($key =~ m/^panic$/io && $options->{$key}) {
		$panic_on_error = 1;
	    } elsif ($key =~ m/^no_warn$/io && $options->{$key}) {
		$no_warn_on_error = 1;
	    } elsif ($key =~ m/^exec$/io && $options->{$key}) {
		$exec = 1;
	    } else {
		$LOGGER->logconfess("Invalid option: $key");
	    }
	}
    }
    my ($output, $retval);
    if (ref($cmd) eq 'ARRAY') {
	$LOGGER->debug(join(' ', @$cmd));
    } else {
	$LOGGER->debug($cmd);	
    }
    if ($always || !$NO_WRITE) {
	if ($exec) {
	    if (ref($cmd) eq 'ARRAY') {
		exec(@$cmd);
	    } else {
		exec($cmd);
	    }
	} else {
	    $output = `$cmd`;
	    $retval = $?;
	}
	if ($retval != 0) {
	    if ($panic_on_error) {
		$LOGGER->logconfess("error running $cmd ($! $retval): $output");
	    } elsif (!$no_warn_on_error) {
		$LOGGER->error("error running $cmd ($! $retval): $output");
	    }
	}
    } else {
        print "NO WRITE: Not running $cmd\n";
    }
    return wantarray ? ($retval, $output) : $output;
}

# ------------------------------------------------------------------------------
# New SVN Commands
#

#
# call svn info on a file and return the fields as a hash
#
# expecting something like this:
# yuanc@casqa1:/u/yuanc/proj/guas/release/src/lib/jsh 2:53pm> svn info gtpub_interface.tcl 
# Path: gtpub_interface.tcl
# Name: gtpub_interface.tcl
# URL: file:///proj/guas/svn/repository/guas/branches/rel_20090417/src/lib/jsh/gtpub_interface.tcl
# Repository Root: file:///proj/guas/svn/repository/guas
# Repository UUID: d3ae617a-c359-11dd-8112-b993bd5e3d76
# Revision: 105821
# Node Kind: file
# Schedule: normal
# Last Changed Author: yuanc
# Last Changed Rev: 105821
# Last Changed Date: 2009-05-08 14:32:20 -0400 (Fri, 08 May 2009)
# Text Last Updated: 2009-05-08 14:32:21 -0400 (Fri, 08 May 2009)
# Checksum: d486aec77a24acb0444c7bba35bedf77
#
#
sub svn_info ( $ ) {
    my ($file) = @_;
    my $cmd = "$SVN info $file";
    my ($error, $output) = run($cmd, {always => 1});
    if ($error) {
	return;
    }
    my %retval;
    foreach my $line (split "\n", $output) {
	# skip blank or empty lines
	if ($line =~ m/^\s*$/) {
	    next;
	}
 	if ($line !~ m/^([^:]*): (.*)$/) {
	    $LOGGER->error("Can't read line of svn info, skipping: $line");
	    next;
	}
	$retval{$1} = $2;
    }
    return \%retval;
}

sub match_repository_root ( $$ ) {
    my ($root, $file) = @_;

    # First, compare the beginning of the file to $root we do this
    # manually rather than using regexps, because root may contain
    # "svn+ssh", which contains a '+', which is a special character
    # for regular expressions.  So, rather than escape all '+'
    # characters, we just do the comparison manually with "ne".
    my $root_len = length($root);
    my $file_root = substr $file, 0, $root_len;
    if ($file_root ne $root) {
	return;
    } else {
	my $file_rest = substr $file, $root_len; 
	return $file_rest;
    }
}


#
# given this information:
#   URL: file:///proj/guas/svn/repository/guas/branches/rel_20090417/src/lib/jsh/gtpub_interface.tcl
#   Repository Root: file:///proj/guas/svn/repository/guas
# get this
#   file:///proj/guas/svn/repository/guas/trunk/src/lib/jsh/gtpub_interface.tcl
#
# relies on the fact that the main trunk is called "trunk"
#
sub get_trunk_file ( $$ ) {
    my ($root, $file) = @_;

    # First, compare the beginning of the file to $root 
    my $file_rest = match_repository_root($root, $file);
    if (!$file_rest) {
	$LOGGER->error("Can't parse release file $file, doesn't start with root $root");
	$LOGGER->error("Are you already in the trunk?");
	return;
    }
    if ($file_rest !~ m@^/branches/rel_\d+(.*)$@) {
	$LOGGER->error("Can't parse release file $file (root $root)");
	$LOGGER->error("Are you already in the trunk?");
	return;
    }
    my $path = $1;

    return $root . "/trunk" . $path;
}

#
# Get the svn root of the latest release branch
#
# relies on the fact that they are of the form $repository_root/branches/rel_YYYYMMDD
#
sub get_latest_release ( $ ) {
    my ($root) = @_;

    my $branch_root = $root . '/branches/';

    my $cmd = "$SVN list $branch_root";
    $LOGGER->debug($cmd);
    my $rc = open(CMD, "$cmd |");
    if (!$rc) {
	$LOGGER->error("Can't run $cmd: $? $! $@");
	return
    }
    my $release_branch = "";
    while (my $line = <CMD>) {
	chomp($line);
	# take the last line that matches
	# relies on the fact that "svn list" outputs release branches in order
	if ($line =~ m@^rel_\d+@) {
	    $release_branch = $line;
	}
    }
    close(CMD)
	or $LOGGER->error("Can't close $cmd: $? $! $@");

    if ($release_branch !~ m@^rel_\d+@) {
	$LOGGER->error("Can't get latest branch from $root (got $release_branch instead)");
	return
    }
    return $branch_root .  $release_branch;
}

#
# given this information:
#   file:///proj/guas/svn/repository/guas/trunk/src/lib/jsh/gtpub_interface.tcl
#   Repository Root: file:///proj/guas/svn/repository/guas
# get this
#   URL: file:///proj/guas/svn/repository/guas/branches/rel_20090417/src/lib/jsh/gtpub_interface.tcl
#
sub get_release_file ( $$ ) {
    my ($root, $file) = @_;

    # First, compare the beginning of the file to $root 
    my $file_rest = match_repository_root($root, $file);
    if (!$file_rest) {
	$LOGGER->error("Can't parse trunk file $file, doesn't start with root $root");
	$LOGGER->error("Are you already in the trunk?");
	return;
    }
    if ($file_rest !~ m@^/trunk(.*)$@) {
	$LOGGER->error("Can't parse trunk file $file (root $root)");
	$LOGGER->error("Are you already in the release branch?");
	return;
    }

    my $branch_root = get_latest_release($root);
    if (!defined($branch_root)) {
	return;
    }

    my $path = $1;

    return $branch_root . "/" . $path;
}

sub get_root_and_full_file($) {
    my ($file) = @_;
    my $svn_info = svn_info($file);
    if (!defined($svn_info)) {
        return;
    }
    if (!defined($svn_info->{"Repository Root"}) ||
        !defined($svn_info->{URL})) {
        $LOGGER->error("Can't get Repository Root or URL from svn info for $file");
        return;
    }
    my $root = $svn_info->{"Repository Root"};
    my $full_file = $svn_info->{URL};
    return ($root, $full_file);
}

sub get_trunk_info_from_branch_file($) {
    my ($file) = @_;
    my ($root, $full_file) = get_root_and_full_file($file);
    my $trunk_file = get_trunk_file($root, $full_file);
    return wantarray ? ($full_file, $trunk_file) : $trunk_file;
}

sub get_branch_info_from_trunk_file($) {
    my ($file) = @_;
    my ($root, $full_file) = get_root_and_full_file($file);
    my $branch_file = get_release_file($root, $full_file);
    return wantarray ? ($full_file, $branch_file) : $branch_file;
}

sub get_cvs_rcs_last_rev ($$) {
    my ($repo_type, $file) = @_;
    my ($rev, $repository_file);
    my $dirname = dirname($file);
    my $basename = basename($file);
    if ($repo_type eq 'rcs') {
        chomp($rev = `rlog -h $file | grep head | cut -d' ' -f 2-`);
    } elsif ($repo_type eq 'cvs') {
        my $CVS_ENTRIES = "$dirname/CVS/Entries";
        unless(open(CVS_ENTRIES, $CVS_ENTRIES)) {
            warn "Can't find CVS Entries file: $CVS_ENTRIES, $!";
            return;
        }
        while (<CVS_ENTRIES>) {
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
    # rev is not necessarily defined
    # it won't be defined if the file doesn't exist or isn't cvs'ed
    # because cvs status will still exist successfully
    return $rev;
}


# given a file under svn control, return the svn revisions where that
# file changed.
sub svn_revision_list($;$) {
    my ($file, $revs_needed) = @_;
    my $cmd = "$SVN log -q $file 2>&1";
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

# Returns git log information.  
#
# Returns an array of arrays.  Each element of the array is a
# 6-element array:
#    [ commit-hash, committer, date, time, tz, msg ]
#
# The order is the same as the order of git log: the first element is
# the most recent commit, the last element is the first commit by
# time.
sub git_revision_list {
    my $format = '"%h %ce %ci %s"';
    my $log = run("$GIT log --pretty=format:$format " . join(' ', @_), {always => 1});
    return [map { 
        my ($hash, $email, $date, $time, $tz, $msg) = split(' ', $_, 6);
        $email =~ s/@(.*)$//;
        [$hash, $email, $date, $msg, $time, $tz];
    } split(/\n/, $log)]
}

# ------------------------------------------------------------------------------
# Functions on "foreign" files, which used to be part of a repository, but were moved
#
sub get_version ( $$ ) {
    my ($file, $repo_type) = @_;

    my %lines;
    foreach my $tag ("Header", "Id", "Source", "HeadURL", "URL") {
	my $cmd = 'grep \$' . $tag . " " . $file;
	chomp($lines{$tag} = run($cmd, {always => 1, no_warn => 1}));
    }
    if (!defined($lines{Header}) && !defined($lines{Id})) {
	$LOGGER->logconfess("Can't get version for $file, no Id or Header tag");
    }

    # fn and version are used as sentinels, so don't initialize them
    my ($fn, $version);
    my ($tag, $date, $time, $user, $other) = ("","","","","","");
    my $data = "";
    # The last tag visited takes precedence...
    foreach my $tag ("Source", "URL", "HeadURL", "Id", "Header") {
	next unless defined($lines{$tag});
	if ($lines{$tag} !~ /\$(.*)\$/) {
	    next;
	}

	$data = $1;
	my ($this_tag, $this_fn, $this_version, $this_date, $this_time, $this_user, $this_other) = split ' ', $data;

	if (!defined($fn) || $tag eq "Header" || $tag eq "Source") {
	    $fn = $this_fn;
	}
	if (defined($this_version)) {
	    $version = $this_version;
	}
	if (defined($this_date)) {
	    $date = $this_date;
	}
	if (defined($this_time)) {
	    $time = $this_time;
	}
	if (defined($this_user)) {
	    $user = $this_user;
	}
	if (defined($this_other)) {
	    $other = $this_other;
	}
    }

    if ((!defined($fn) || !defined($version)) && $repo_type eq "cvs") {
	my $base = basename($file);
	my $dir = dirname($file);
	if ($base =~ m/^\.#(\S+)\.(\d\.[\d\.]+)$/) {
	    $fn = $1;
	    $version = $2;
	    chomp(my $repos = `cat $dir/CVS/Root`);
	    $repos .= "/";
	    chomp($repos .= `cat $dir/CVS/Repository`);
	    $fn = $repos . "/" . $fn;
	}
    }

    if (!defined($fn) || !defined($version)) {
	$LOGGER->logconfess("Can't get version or repository for $file, malformed cvs tags: " . Dumper(%lines));
    }

    # strip trailing ,v from the repository file
    $fn =~ s/,v$//g;

    # split the fn into the repository and the rest
    my $repository;
    if ($fn =~ m@^(.*)repository/(.*)$@) {
	$repository = $1 . "repository";
	$fn = $2;
    } else {
	$repository = "";
    }

    $LOGGER->debug(join('', map { $_ . "\n" } ("data       => $data", 
				      "repository => $repository",
				      "fn         => $fn", 
				      "version    => $version", 
				      "date       => $date", 
				      "time       => $time", 
				      "user       => $user", 
				      "other      => $other")));
    return ($repository, $fn, $version);
}

# ------------------------------------------------------------------------------
# My added subcommands
#

sub lastrev($$$$$$) {
    my ($repo_type, $action, $cmd_options, $files, 
        $lastrev_arg_revs_back, $lastrev_arg_revno) = @_;

    $lastrev_arg_revs_back //= 1;
    if (scalar(@$files) == 0 && ($repo_type eq 'svn' || $repo_type eq 'git')) {
        # A file of "" will do whatever the log and diff commands will
        # do with no arguments.  For svn, it will show the log or diff
        # of the current directory.  For git, it will show the log or
        # diff of the whole repo.  Since RCS and CVS are file based,
        # you can't run log and diff without files.
        push(@$files, "");
    }
    foreach my $file (@$files) {
        # run get_repo_type again on each file, so we can handle files
        # on different repositories.
        my $repo_type = get_repo_type($repo_type, $action, [$file]);
        
        if ($repo_type eq 'svn') {
            my $prev;
            my $revno = $lastrev_arg_revno;
            if ($lastrev_arg_revs_back != 1) {
                my $rev_list = svn_revision_list($file, $lastrev_arg_revs_back);
                if (defined($rev_list)) {
                    if (scalar(@$rev_list) >= $lastrev_arg_revs_back) {
                        if (defined($revno)) {
                            $LOGGER->warn("specified both revs_back and revno -- ignoring revno $revno");
                        }
                        $revno = $rev_list->[$lastrev_arg_revs_back-1];
                    } else {
                        $LOGGER->logconfess("Not enough revisions: $lastrev_arg_revs_back, " . scalar(@$rev_list));
                    }
                }
            }
            if (defined($revno)) {
                $revno =~ s/^r//;
                $prev = $revno - 1;
            } else {
                $prev = "PREV";
                $revno = "COMMITTED";
            }
            my $output = run("svn log -r$prev:$revno $file");
            print $output if defined($output);
            $output = run("svn diff -r$prev:$revno $file");
            print $output if defined($output);
        } elsif ($repo_type eq 'cvs' ||
                 $repo_type eq 'rcs') {
            my $last_revision;
            if (defined($lastrev_arg_revno)) {
                $last_revision = $lastrev_arg_revno;
            } else {
                $last_revision = get_cvs_rcs_last_rev($repo_type, $file)
            }
            if (!defined($last_revision) || $last_revision eq "") {
                $LOGGER->warn("skipping $file");
                next;
            } else {
                print "$last_revision\n";
            }
            my @rev_nos = split(/\./, $last_revision);
            $rev_nos[$#rev_nos] -= $lastrev_arg_revs_back;
            die "Not enough revisions: $last_revision" if ($rev_nos[$#rev_nos] < 1);
            my $prev_revision = join(".", @rev_nos);
            if ($lastrev_arg_revs_back > 1) {
                $rev_nos[$#rev_nos]++;
                $last_revision = join(".", @rev_nos);
            }
	
            if ($repo_type eq 'rcs') {
                my $output = run("rlog -r$last_revision $file");
                print $output if defined($output);
                $output = run("rcsdiff -u -r$prev_revision -r$last_revision $file", {no_warn=>1});
                print $output if defined($output);
            } else {
                my $log  = 'log';
                my $diff = 'diff';
                if ($action eq 'rlastrev') {
                    $log  = 'rlog';
                    $diff = 'rdiff';
                }
                my $cmd_options_str = join(' ', @$cmd_options);
                my $output = run("cvs $cmd_options_str $log -r$last_revision $file");
                print $output if defined($output);
                $output = run("cvs $cmd_options_str $diff -u -r $prev_revision -r $last_revision $file", {no_warn=>1});
                print $output if defined($output);
            }
        } elsif ($repo_type eq 'git') {
            # You would think that for git, this would be trivial --
            # just convert "lastrev -b 3" into "git show -n 1
            # HEAD^^^".  But that doesn't work because HEAD^ is the
            # previous commit for the whole repository, not the
            # previous commit that touched this file.
            my $revno = $lastrev_arg_revno;
            my $file_hash = [$file];
            cd_to_git_repo($file_hash);
            $file = $file_hash->[0];
            if ($lastrev_arg_revs_back != 1) {
                my $rev_list = git_revision_list($file);
                if (defined($rev_list)) {
                    if (scalar(@$rev_list) >= $lastrev_arg_revs_back) {
                        if (defined($revno)) {
                            $LOGGER->warn("specified both revs_back and revno -- ignoring revno $revno");
                        }
                        $revno = $rev_list->[$lastrev_arg_revs_back-1][0];
                    } else {
                        $LOGGER->logconfess("Not enough revisions: $lastrev_arg_revs_back, " . scalar(@$rev_list));
                    }
                }
            }
            if (!defined($revno)) {
                $revno = 'HEAD';
            }
            my $output = run("git show -n 1 $revno $file");
            print $output if defined($output);
        }
    }
}

sub switch_to_release($$$$) {
    my ($repo_type, $action, $files, $run_cmds) = @_;
    
    if ($repo_type ne "svn") {
	$LOGGER->logconfess("$action is only valid with svn");
    }
    foreach my $file (@$files) {
        my ($full_file, $branch_file) = get_branch_info_from_trunk_file($file);
	if (!defined($branch_file)) {
	    next;
	}

	my $cmd = "$SVN switch $branch_file $file";
	if ($run_cmds) {
	    print "Running: $cmd\n";
	    my $output = run($cmd);
	    print $output;
	} else {
	    print $cmd . "\n";
	}
    }
}

sub switch_to_trunk($$$$) {
    my ($repo_type, $action, $files, $run_cmds) = @_;

    if ($repo_type ne "svn") {
	$LOGGER->logconfess("$action is only valid with svn");
    }
    foreach my $file (@$files) {
        my ($full_file, $trunk_file) = get_trunk_info_from_branch_file($file);
	if (!defined($trunk_file)) {
	    next;
	}

	my $cmd = "$SVN switch $trunk_file $file";
	if ($run_cmds) {
	    print "Running: $cmd\n";
	    my $output = run($cmd);
	    print $output;
	} else {
	    print $cmd . "\n";
	}
    }
}

sub update_from_trunk($$$$$) {
    my ($repo_type, $action, $files, $run_cmds, $uptrunk_arg_revision) = @_;

    if ($repo_type ne "svn") {
	$LOGGER->logconfess("$action is only valid with svn");
    }
    foreach my $file (@$files) {
        my ($full_file, $trunk_file) = get_trunk_info_from_branch_file($file);
	if (!defined($trunk_file)) {
	    next;
	}

	my $cmd;
	if (1) {
            my $rev;
            if (defined($uptrunk_arg_revision)) {
                $rev = $uptrunk_arg_revision;
            } else {
                # To merge just the last revision of the trunk file
                my $trunk_svn_info = svn_info($trunk_file);
                if (!defined($trunk_svn_info)) {
                    next;
                }
                if (!defined($trunk_svn_info->{"Last Changed Rev"})) {
                    $LOGGER->error("Can't get Last Changed Rev from svn info for $trunk_file");
                    next;
                }
                $rev = $trunk_svn_info->{"Last Changed Rev"};
            }
	    $cmd = "$SVN merge -c$rev $trunk_file $file";
	    # or, equivalently:
	    # my $prev = $rev-1;
	    # print "$SVN merge -r$prev:$rev $trunk_file $file\n";
	} else {
	    # To merge all changes from the trunk to the release file
	    $cmd = "$SVN merge $full_file $trunk_file $file";
	}
	if ($run_cmds) {
	    print "Running: $cmd\n";
	    my $output = run($cmd);
	    print $output;
	} else {
	    print $cmd . "\n";
	}
    }

    #
    # Note, to undo an update, you can't just remove the file and svn
    # up it again.  That will leave it in a state where it isn't
    # different, but the tags are different, so trying to do the merge
    # again won't work.  You have to do "svn revert <file>".
    #
}

sub release_message($$$) {
    my ($repo_type, $action, $files) = @_;

    if ($repo_type ne "svn") {
	$LOGGER->logconfess("$action is only valid with svn");
    }

    # print out a message for committing into the release branch.  get
    # the commit message of the normal branch, then add 
    # "pushing <revision> into production" to the front

    foreach my $file (@$files) {
        my ($full_file, $trunk_file) = get_trunk_info_from_branch_file($file);
	if (!defined($trunk_file)) {
	    next;
	}

        # To merge just the last revision of the trunk file
        my $trunk_svn_info = svn_info($trunk_file);
        if (!defined($trunk_svn_info)) {
            next;
        }
        if (!defined($trunk_svn_info->{"Last Changed Rev"})) {
            $LOGGER->error("Can't get Last Changed Rev from svn info for $trunk_file");
            next;
        }
        my $rev = $trunk_svn_info->{"Last Changed Rev"};
        my $cmd = "$SVN log -c$rev $trunk_file";
        print "Running: $cmd\n";
        my $msg = run($cmd, {always => 1});

        my @lines = split("\n", $msg);

        # remove the extra info besides the log message
        shift(@lines);
        shift(@lines);
        pop(@lines);
        unshift(@lines, "", "pushing revision $rev into production");
        print join("\n", @lines) . "\n";
    }
}

sub foreign_diff ($$$$$$) {
    my ($repo_type, $action, $files, 
        $foreign_arg_repos,
        $foreign_arg_fn,
        $foreign_arg_version) = @_;

    if ($repo_type ne 'svn' and $repo_type ne 'cvs') {
	$LOGGER->logconfess("'$action' is only implemented for svn and cvs, not $repo_type");
    }

    foreach my $file (@$files) {
	my ($repository, $fn, $version);
	if (defined($foreign_arg_repos) &&
	    defined($foreign_arg_fn) &&
	    defined($foreign_arg_version)) {
	    $repository = $foreign_arg_repos;
	    $fn = $foreign_arg_fn;
	    $version = $foreign_arg_version;
	} else {
	    ($repository, $fn, $version) = get_version($file, $repo_type);
	}
	$LOGGER->debug("file $file => repository: $repository fn:$fn vers:$version");

	if ($repository eq "") {
	    # Even knowing the repository wouldn't be enough because
	    # the fn needs to be the full path from the repository to
	    # the file (e.g. bin/share/foo.pl) not just the base name.
	    # This is needed for both svn and cvs.
	    $LOGGER->logconfess("Can't get repository from file name $fn for file $file");
	}

	my $cmd;
	if ($repo_type eq "svn") {
	    $cmd = "$SVN cat -r $version $repository/$fn | $DIFF -u - $file";
	} else {
	    $cmd = "$CVS -d $repository checkout -r $version -p $fn | $DIFF -u - $file";
	}
	# save the output to a variable before printing to force
	# scalar context
	my $output = run($cmd, {no_warn => 1});
	print $output;
    }
}

sub foreign_merge($$$) {
    my ($repo_type, $action, $files) = @_;
    if (scalar(@$files) < 2) {
	$LOGGER->logconfess("'$action' requires at least two arguments: \n" . 
              "  $0 $action [repository_file]* [foreign_file_or_dir]\n" . 
              "got: " .  join(',', @$files));
    }

    if ($repo_type ne 'svn' and $repo_type ne 'cvs') {
	$LOGGER->logconfess("'$action' is only implemented for svn and cvs, not $repo_type");
    }
    if (!defined($CMDS{$repo_type})) {
	$LOGGER->logconfess("Invalid repo_type $repo_type");
    }
    my $cmd = $CMDS{$repo_type};

    my @repository_files = @$files;
    my $foreign_file_or_dir = pop(@repository_files);

    if (scalar(@repository_files) > 1 && ! -d $foreign_file_or_dir) {
	$LOGGER->logconfess("When '$action' is called on multiple files, the last argument must be a directory: $foreign_file_or_dir");
    }
    foreach my $repository_file (@repository_files) {
	#
	# Assert that the repository file is up to date so that we
	# don't clobber any local changes.
	#
	if ($repo_type eq "cvs") {
	    chomp(my $line = run("$cmd status $repository_file | grep Status | grep Up-to-date", 
                                 {always => 1, no_warn => 1}));
	    if ($line eq "") {
		$LOGGER->logconfess("$repository_file is not up to date");
	    }
	} else {
	    chomp(my $line = run("$cmd status -u $repository_file | grep -v 'Status against revision'", 
                                 {always => 1, no_warn => 1}));
	    if ($line ne "") {
		$LOGGER->logconfess("$repository_file is not up to date");
	    }
	}

	#
	# Assert that the foreign file exists and is readable
	# 
	my $foreign_file = $foreign_file_or_dir;
	if (-d $foreign_file_or_dir) {
	    $foreign_file .= '/' . basename($repository_file);
	}

	if (! -r $foreign_file) {
	    $LOGGER->logconfess("Can't find $foreign_file ($repository_file, $foreign_file_or_dir)");
	}
    }

    foreach my $repository_file (@repository_files) {
	my $foreign_file = $foreign_file_or_dir;
	if (-d $foreign_file_or_dir) {
	    $foreign_file .= '/' . basename($repository_file);
	}

	#
	# If we don't own the foreign file, it's ok, but only copy the
	# foreign file to our local checkout, don't remove the
	# original foreign file.
	# 
	my $copy_instead_of_move = 0;
	if (! -o $foreign_file) {
	    $copy_instead_of_move = 1;
	}

	#
	# Now the meat of it: update to the original version, move the
	# file over, then update to the Head revision
	# 
	my ($repository, $fn, $version) = get_version($foreign_file, $repo_type);
	run("$cmd up -r $version $repository_file");
	if ($copy_instead_of_move) {
	    run("cp -f $foreign_file $repository_file");
	} else {
	    run("mv -f $foreign_file $repository_file");
	}
	if ($repo_type eq "svn") {
	    run("$cmd up -rHEAD $repository_file");
	} else {
	    run("$cmd up -A $repository_file");
	}
    }
}

#
# Let's say a line was removed from a file, and you want to know the
# last time that line existed in the file:
#
#   vc grep-hist <patt> <file>
#
# will go through history from most recent to oldest, and print
# matches.
#
sub grep_hist($$$$$$) {
    my ($repo_type, $action, $options, $files, 
        $show_missing, $first_occur, $last_occur) = @_;
    if ($repo_type ne 'git') {
        $LOGGER->logconfess("grep-hist is only implemented for git");
    }
    if (scalar(@$files) < 1) {
        $LOGGER->logconfess("grep-hist takes at least one args: " . join(' ', @$files));
    }
    $options = join(' ', @$options);
    my $cmd = $CMDS{$repo_type};

    my $patt = shift(@$files);
    if (scalar(@$files) == 0) {
        push(@$files, "");
    } else {
        cd_to_git_repo($files);
    }
 FILE:
    foreach my $file (@$files) {
        my $revs = git_revision_list($file);
        my $prev;
        foreach my $rev (@$revs) {
            my ($hash, $email, $date, $msg) = @$rev;
            my $output = run("$cmd grep $options '$patt' $hash $file", {no_warn => 1});
            if ($first_occur || $last_occur) {
                if (($first_occur && $output eq "") || ($last_occur && $output ne "")) {
                    if (defined($prev)) {
                        lastrev($repo_type, 'lastrev', [], [$file], undef, $prev);
                        next FILE;
                    }
                } else {
                    $prev = $hash;
                }
            }
            elsif ($show_missing) {
                if ($output eq "") {
                    print join(' ', $hash, $email, $date, $msg) . "\n";
                }
            }
            else {
                if ($output ne "") {
                    print join(' ', $email, $date) . "\n";
                    print $output;
                }
            }
        }
        if (($first_occur || $last_occur) && defined($prev)) {
            lastrev($repo_type, 'lastrev', [], [$file], undef, $prev);
        }
    }
}

#
# Run a bisect command across the whole repository history.
#
# For example, to find the first time a line appears in a file, run
# this:
# 
#   vc bisect-all true_if_failure git grep <pattern> <file>
#
# (the only problem is that this might not work if the command
# "true_if_failure" is part of the current repository because the
# repository will have been rewound to an earlier state where
# true_if_failure might not exist)
#
sub bisect_all($$$$) {
    my ($repo_type, $action, $options, $args) = @_;
    if ($repo_type ne 'git') {
        $LOGGER->logconfess("bisect-all is only implemented for git");
    }
    if (scalar(@$args) < 1) {
        $LOGGER->logconfess("bisect-all takes at least one args: " . join(' ', @$args));
    }
    # this will change the contents of $args
    cd_to_git_top($args);
    my $cmd = join(' ', map {"'$_'"} (@$options, @$args));
    my $revs = git_revision_list();
    run('git bisect start');
    run('git bisect bad');
    run('git bisect good ' . $revs->[$#$revs][0]);
    my $output = run('git bisect run ' . $cmd);
    print $output;
    run('git bisect reset');
}

# ------------------------------------------------------------------------------
# If it isn't one of the added subcommands, it's one of the standard
# subcommands.  But we still modify the arguments a little.
#

# Modifies in place the array that $subcmd_options is a reference to.  
sub customize_subcmd_options($$$$$$$$) {
    my ($repo_type, $action, $subcmd_options,
        $diff_arg_u, $diff_arg_w, 
        $ann_arg_v, 
        $up_arg_d, $up_arg_P) = @_;

    if (!defined($action)) {
        return;
    }

    if ($repo_type eq "svn") {
        if ($action eq "diff" && ($diff_arg_u || $diff_arg_w)) {
            if ($diff_arg_u && !$diff_arg_w) {
                # alternatively, could replace it with -x -u, but -u seems to be
                # on by default, so it's not necessary.
                $LOGGER->warn("Ignoring -u argument to svn diff");
            } else {
                $LOGGER->warn("Adding -x argument to svn diff");
                if ($diff_arg_u) {
                    unshift(@$subcmd_options, '-u');
                }
                if ($diff_arg_w) {
                    unshift(@$subcmd_options, '-w');
                }
                unshift(@$subcmd_options, '-x');
            }
        } elsif ($action eq "annotate" || $action eq "ann" || $action eq "blame" || $action eq "praise") {
            if (!$ann_arg_v) {
                $LOGGER->warn("Adding -v to svn annotate");
            }
            unshift(@$subcmd_options, '-v');
        } elsif (($action eq "up" || $action eq "update") && ($up_arg_d || $up_arg_P)) {
            if ($up_arg_d) {
                $LOGGER->warn("Removing -d from svn up");
            }
            if ($up_arg_P) {
                $LOGGER->warn("Removing -P from svn up");
            }
        }
    } elsif ($repo_type eq "cvs") {
        if ($action eq "diff") {
            if (!$diff_arg_u) {
                $LOGGER->warn("Adding -u argument to cvs diff");
            }
            # We unshift rather than push because if the arguments are:
            #
            #   cvs diff -r A -r B
            #
            # then our logic will recognize -r as an option, but the
            # prescence of A will make it think that the options are
            # concluded.  If we just stuck "-u" at the end of the
            # options, we'd get:
            #
            #   cvs diff -r -u A -r B
            #
            # which would be wrong.  If we unshift the -u, we get:
            #
            #   cvs diff -u -r A -r B
            #
            # which is better.  We just avoid the issue of having the
            # understand that -r requires an argument.            
            unshift(@$subcmd_options, '-u'); 
        } elsif (($action eq "up" || $action eq "update") && ($up_arg_d || $up_arg_P)) {
            if ($up_arg_d) {
                unshift(@$subcmd_options, '-d');
            }
            if ($up_arg_P) {
                unshift(@$subcmd_options, '-P');
            }
        }
    } elsif ($repo_type eq "rcs") {
        if ($action eq "diff") {
            if (!$diff_arg_u) {
                $LOGGER->warn("Adding -u argument to rcs diff");
            }
            unshift(@$subcmd_options, '-u'); 
        }
    }

    if ($action ne "diff") {
        unshift(@$subcmd_options, '-u') if ($diff_arg_u);
        unshift(@$subcmd_options, '-w') if ($diff_arg_w);
    }
    if ($action ne "ann" && 
        $action ne "praise" && 
        $action ne "blame" && 
        $action ne "annotate") 
    {
        unshift(@$subcmd_options, '-v') if ($ann_arg_v);
    }
    if ($action ne "up" && $action ne "update") {
        unshift(@$subcmd_options, '-d') if ($up_arg_d);
        unshift(@$subcmd_options, '-P') if ($up_arg_P);
    }

    $LOGGER->debug("new subcmd_options = '" . join(', ', @$subcmd_options) . "'");
}

sub get_command($$) {
    my ($repo_type, $action) = @_;
    if ($repo_type eq 'rcs') {
        if ($action eq 'log') {
            return ('rlog', undef);
        } elsif ($action eq 'diff') {
            return ('rcsdiff', undef);
        } elsif (scalar(grep {$action eq $_} qw(ann annotate blame)) > 0) {
            return ('blame', undef);
        }
    }

    if (!defined($CMDS{$repo_type})) {
        $LOGGER->logconfess("Invalid repository type $repo_type (should be one of " . join(',', keys(%CMDS)) . ")");
    }
    return ($CMDS{$repo_type}, $action);
}

#
# Git commands must be run from a git repository, so this will cd into
# the directory of the first file given.
#
# This command changes the contents of the $files array ref that it is
# given.  It converts paths into absolute paths, so that things will
# still work after the cd.
#
sub cd_to_git_repo($) {
    my ($files) = @_;
    my $dir;
    for (my $ii = 0; $ii < scalar(@$files); $ii++) {
        if (! -f $files->[$ii]) {
            next;
        }
        my $abs_path = abs_path($files->[$ii]);
        $LOGGER->debug("$files->[$ii] => $abs_path");
        $files->[$ii] = $abs_path;
        if (!defined($dir)) {
            $dir = my_dirname($files->[$ii]);
        }
    }
    if (defined($dir)) {
        $LOGGER->info("chdir $dir");
        chdir $dir;
    }
}

#
# Some git commands must be run from the top of the git repository.  
#
# This command changes the contents of the $files array ref that it is
# given.  It converts paths so they are relative to the git top so
# that things will work after the cd.
#
sub cd_to_git_top($) {
    my ($files) = @_;
    if (!defined($files) || scalar(@$files) == 0) {
        return;
    }
    my $dir = get_git_top($files->[$#$files]);
    if (!defined($dir)) {
        return;
    }
    $dir = abs_path($dir);

    for (my $ii = 0; $ii < scalar(@$files); $ii++) {
        if (! -f $files->[$ii]) {
            next;
        }
        my $abs_path = abs_path($files->[$ii]);
        $abs_path =~ s@^$dir/@@;
        $LOGGER->debug("$files->[$ii] => $abs_path");
        $files->[$ii] = $abs_path;
    }
    $LOGGER->info("chdir $dir");
    chdir $dir;
}

sub run_modified_command($$$$$$$$$$) {
    my ($repo_type, $cmd_options, $action, $subcmd_options, $files,
        $diff_arg_u, $diff_arg_w, 
        $ann_arg_v, 
        $up_arg_d, $up_arg_P) = @_;

    my $cmd;
    ($cmd, $action) = get_command($repo_type, $action);
    
    my @cmd = ($cmd, @$cmd_options);
    if (defined($action)) {
        push(@cmd, $action);
    }
    if ($repo_type eq 'git') {
        cd_to_git_repo($files);
    }
    push(@cmd, @$subcmd_options, @$files);
    run(\@cmd, {exec => 1});
}

# ------------------------------------------------------------------------------
# Run it!
#

main();

# ------------------------------------------------------------------------------

__END__

=head1 AUTHOR

 Conan Yuan

=cut

