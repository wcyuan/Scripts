#!/usr/bin/env perl
#

=head1 NAME

git-big-update.pl - update across multiple branches, trees, etc

=head1 SYNOPSIS

  git-big-update.pl

  Options:
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

=item I<debug>

Print commands, don't run them.

=back

=head1 DESCRIPTION

pull across multiple repos and branches

=cut

use strict;
use warnings 'all';
use Getopt::Long qw(GetOptions);
use Carp;
use Cwd;

# --------------------------------------------

my $DEBUG = 0;

sub linux($);

my @TREE = ([linux('/u/yuanc/proj/eomm'),
             [['master',                    'git svn rebase'],
              ['rel_20130515-svn',          'git svn rebase'],
              ['git-default',               'git pull'],
              ['add-pcap',                  'git pull'],
              ['parallel_result_tree_diff', 'git pull']]],
            [linux('/u/yuanc/proj/scratcheomm'),
             [['master',                    'git pull'],
              ['git-fastsim',               'git pull'],
              ['two_forecasts',             'git pull']]],
            ['/c/dev/deshaw/git/eomm',
             [['master',                    'git pull'],
              ['add-pcap',                  'git pull']]]);

sub main() {
    my ($all) = parse_command_line();

    foreach my $repo_info (@TREE) {
        my ($repo, $branches) = @$repo_info;
        if (! -e ($repo)) {
            warn("Skipping $repo, not accessible.");
            next;
        }
        if (!$all) {
            if (getcwd() !~ m/^$repo/) {
                warn("Skipping $repo, not our cwd.");
                next;
            }
        }
        cd($repo);
        foreach my $branch_info (@$branches) {
            my $orig = current_branch();
            my $stashed = 0;
            if (needs_stash()) {
                run('git stash');
                $stashed = 1;
            }
            my ($branch, $cmd) = @$branch_info;
            run("git checkout $branch");
            run($cmd);
            run("git checkout $orig");
            if ($stashed) {
                run('git stash pop');
            }
        }
    }
}


# --------------------------------------------

sub parse_command_line() {
    # Parse any command-line options
    GetOptions('debug|no_write!'  => \$DEBUG,
               'all!'             => \my $all)
        or die("Bad arguments");

    pod2usage("Wrong number of arguments") unless @ARGV < 1;

    return $all
}

# --------------------------------------------
# System helpers

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

sub cd($) {
    my ($dir) = @_;

    print("cd $dir\n");
    chdir($dir)
        or confess("Can't cd to $dir");
}

sub linux($) {
    my ($path) = @_;
    if ($^O ne 'linux') {
        return '/n' . $path;
    }
    return $path;
}

# --------------------------------------------
# Git helpers

sub current_branch() {
    my $orig = run('git branch | grep ^*',
                   {always => 1, no_die_on_error => 1, return_output => 1});
    chomp($orig);
    $orig =~ s/^\* //;
    if (!defined($orig) || $orig eq '') {
        confess("Can't get current branch");
    }
    return $orig;
}

sub needs_stash() {
    return !run('git diff --quiet HEAD', {always => 1, no_die_on_error => 1});
}

# --------------------------------------------

main();

# --------------------------------------------
