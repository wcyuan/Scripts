#!/usr/bin/env perl
#

=head1 NAME

git-cherry-push.pl - cherry-pick a single local commit and push it

=head1 SYNOPSIS

  git-cherry-push.pl [options] <rev>

  Options:
    --release         push it to the release tree
    --both            push it to both the master and release trees
    --help, -?        shows brief help message
    --perldoc         shows full documentation

  See also Deshaw::Getopt::Long for complete standard options list.

=head1 ARGUMENTS

=over

=item I<rev>

The revision to push

=back

=head1 OPTIONS

=over 4

=item I<--release>

Push it to the release tree.  This assumes we are in a GUAS repo.

=item I<--both>

Push it to both the master and release trees

=item I<--help>

Print a brief help message and exit.

=item I<--perldoc>

Print the perldoc page and exit.

=back

=head1 DESCRIPTION

For master (assumes we want to push to remote/origin)

    o We assume that we are in a git repo
    o create a new branch tracking remote/origin
    o git stash (if necessary)
    o switch to that branch
    o git cherry-pick the revision
    o git pull
    o git push
    o switch back to the original branch
    o git pull
    o git stash pop (if necessary)
    o delete temp branch

For release (assumes a particular repository):

    o cd to release tree
    o git pull
    o git cherry-pick the revision
    o git push
    o cd to shared repository
    o git pull

=cut

use strict;
use warnings 'all';
use Getopt::Long qw(GetOptions);
use Carp;

# --------------------------------------------

my $DEBUG = 0;
my $SHARED_RELEASE = '/testbed/github/release';

sub main() {
    my ($rev, $master, $release, $release_tree, $upstream, $leave) =
        parse_command_line();

    if ($master) {
        push_to_master($rev, $upstream, $leave);
    }

    if ($release) {
        push_to_release($rev, $release_tree);
    }
}

# --------------------------------------------

sub parse_command_line() {
    my $release_tree = $SHARED_RELEASE;

    my $user = getpwuid($>) || getpwuid($<) || getlogin();
    if ($user eq 'yuanc') {
        $release_tree = '/home/Yuan/testbed/github/release';
    }

    # Parse any command-line options
    GetOptions('master!'          => \my $master,
               'release!'         => \my $release,
               'both!'            => \my $both,
               'upstream=s'       => \my $upstream,
               'leave!'           => \my $leave,
               'debug|no_write!'  => \$DEBUG)
        or die("Bad arguments");

    #
    # no options means just do the master branch
    # -master    means just do the master branch
    # -release   means just do the release branch
    # -both      means do both branches
    #

    if ($both) {
        $master = 1;
        $release = 1;
    } else {
        if (!defined($master)) {
            if ($release) {
                $master = 0;
            } else {
                $master = 1;
            }
        }
    }

    pod2usage("Wrong number of arguments") unless @ARGV <= 1;

    my ($rev) = @ARGV;

    if (!defined($rev)) {
        $rev = run('git log --pretty=format:%H -n 1',
                   {always => 1, return_output => 1});
    }

    my $msg = run("git log -n 1 $rev",
                  {always => 1, return_output => 1});
    print "Pushing rev $msg\n";

    return ($rev, $master, $release, $release_tree, $upstream, $leave);
}

sub run($;$) {
    my ($cmd, $opts) = @_;

    if ($DEBUG && !$opts->{always}) {
        print("Would run: $cmd\n");
        return 1;
    } else {
        print("Running: $cmd\n");
        if ($opts->{return_output}) {
            my $output = `$cmd`;
            my $rc = $?;
            if (!$opts->{no_die_on_error} && $rc != 0) {
                confess("Error running $cmd: $rc $@ $!");
            }
            return wantarray ? ($output, $rc) : $output;
        } else {
            my $rc = system($cmd);
            if (!$opts->{no_die_on_error} && $rc != 0) {
                confess("Error running $cmd: $rc $@ $!");
            }
            return $rc == 0;
        }
    }
}

sub current_branch() {
    my $orig = run('git symbolic-ref --short HEAD',
                   {always => 1, no_die_on_error => 1, return_output => 1});
    chomp($orig);
    if (!defined($orig) || $orig eq '') {
        confess("Can't get current branch");
    }
    return $orig;
}

sub needs_stash() {
    return !run('git diff --quiet HEAD', {always => 1, no_die_on_error => 1});
}

sub upstream() {
    return run('git rev-parse --abbrev-ref @{upstream}',
               {always => 1, return_output => 1});
}

sub push_to_master($;$$) {
    my ($rev, $upstream, $leave) = @_;

    my $orig = current_branch();
    if (!defined($upstream)) {
        $upstream = upstream();
    }
    my $stashed = 0;
    if (needs_stash()) {
        run('git stash');
        $stashed = 1;
    }
    run("git branch --track temp $upstream");
    run('git checkout temp');
    my $rc = run("git cherry-pick $rev", {no_die_on_error => !$leave});
    if (!$DEBUG && !$rc) {
        print("\nError running cherry-pick, aborting.  To be left in the " .
              "middle of the conflict, use the --leave option.\n");
        run('git reset --merge');
    } else {
        run('git pull');
        my $rc = run("git push", {no_die_on_error => !$leave});
        if (!$DEBUG && !$rc) {
            print("\nError running push, aborting.  To be left in the " .
                  "middle of the conflict, use the --leave option.\n");
            run('git reset --merge');
        }
    }
    run("git checkout $orig");
    run('git pull');
    if ($stashed) {
        run('git stash pop');
    }
    run('git branch -D temp');
}

sub cd($) {
    my ($dir) = @_;

    print("cd $dir\n");
    chdir($dir)
        or confess("Can't cd to $dir");
}

sub push_to_release($$) {
    my ($rev, $release_tree) = @_;

    cd($release_tree);

    run('git pull');
    run("git cherry-pick $rev");
    run("git push");

    if ($release_tree ne $SHARED_RELEASE) {
        cd($SHARED_RELEASE);
        run('git pull');
    }
}

# --------------------------------------------

main();

# --------------------------------------------
