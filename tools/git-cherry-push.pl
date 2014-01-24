#!/usr/bin/env perl
#

=head1 NAME

git-cherry-push.pl - cherry-pick a single local commit and push it

=head1 SYNOPSIS

  git-cherry-push.pl [options] <rev>

  Options:
    --help, -?        shows brief help message
    --perldoc         shows full documentation

  See also Deshaw::Getopt::Long for complete standard options list.

=head1 ARGUMENTS

=over

=item I<rev>

The revision to push (optional, defaults to the HEAD revision)

=back

=head1 OPTIONS

=over 4

=item I<--upstream [remote/branch]>

Specify the upstream branch to push to

=item I<--leave>

If there is an error, don't clean up, leave it in the conflicted state
so the user can investigate.

=item I<--help>

Print a brief help message and exit.

=item I<--perldoc>

Print the perldoc page and exit.

=back

=head1 DESCRIPTION

    o We assume that we are in a git repo
    o create a new temp branch tracking the upstream of the current branch
    o git stash (if necessary)
    o switch to the temp branch
    o git cherry-pick the revision
    o git pull
    o git push
    o switch back to the original branch
    o git pull
    o git stash pop (if necessary)
    o delete temp branch

=cut

use strict;
use warnings 'all';
use Getopt::Long qw(GetOptions);
use Carp;

# --------------------------------------------

my $DEBUG = 0;

sub main() {
    my ($rev, $upstream, $leave) = parse_command_line();

    pick_and_push($rev, $upstream, $leave);
}

# --------------------------------------------

sub parse_command_line() {
    # Parse any command-line options
    GetOptions('upstream=s'       => \my $upstream,
               'leave!'           => \my $leave,
               'debug|no_write!'  => \$DEBUG)
        or die("Bad arguments");

    pod2usage("Wrong number of arguments") unless @ARGV <= 1;

    my ($rev) = @ARGV;

    if (!defined($rev)) {
        $rev = '';
    }
    # $rev can be anything that git log understands, including a
    # filename (in which case we'll push the last committed change to
    # that file)
    $rev = run("git log --pretty=format:\%H -n 1 $rev",
               {always => 1, return_output => 1});

    my $msg = run("git log -n 1 $rev",
                  {always => 1, return_output => 1});
    print "Pushing rev $msg\n";

    return ($rev, $upstream, $leave);
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

sub pick_and_push($;$$) {
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
        run("git checkout $orig");
    } else {
        run('git pull');
        my $rc = run("git push", {no_die_on_error => !$leave});
        if (!$DEBUG && !$rc) {
            print("\nError running push, aborting.  To be left in the " .
                  "middle of the conflict, use the --leave option.\n");
            run('git reset --merge');
            run("git checkout $orig");
        } else {
            run("git checkout $orig");
            run('git pull');
        }
    }
    if ($stashed) {
        run('git stash pop');
    }
    run('git branch -D temp');
}

# --------------------------------------------

main();

# --------------------------------------------
