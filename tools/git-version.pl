#!/usr/local/bin/perl -w
#
# My version of
# http://stackoverflow.com/questions/223678/which-commit-has-this-blob
#

use strict;
use Getopt::Long;
use Log::Log4perl qw(:levels);
use File::Basename qw(basename);

# --------------------------------------------

my @REPOS = qw(/proj/tools/build/periodic/guas/master);
Log::Log4perl->easy_init($ERROR);
my $LOGGER = Log::Log4perl->get_logger();

# --------------------------------------------

sub main() {

    GetOptions("diff!" => \my $diff,
               "verbose" => sub { $LOGGER->level($DEBUG) });

    foreach my $file (@ARGV) {
        if (!-f $file) {
            $file = find_in_path($file);
        }
        foreach my $repo (@REPOS) {
            $LOGGER->debug("chdir($repo)");
            chdir($repo);
            my ($path, $commit, $user, $date, $subject) = find_commit($file);
            if ($diff) {
                exec("git show -n 1 $commit $path");
            } else {
                print "$commit $user $date\n";
                print "$repo/$path\n";
                print "$subject\n";
            }
        }
    }
}

# --------------------------------------------
# Quick git commands
#

sub git_present_in_repo($) {
    my ($hash) = @_;
    my $cmd = "git cat-file -t $hash 2>&1";
    $LOGGER->debug($cmd);
    chomp(my $reply = `$cmd`);
    if ($? == 0 && $reply eq 'blob') {
        return 1;
    } else {
        return;
    }
}

sub git_hash($) {
    my ($file) = @_;
    my $cmd = "git hash-object $file";
    chomp(my $hash = `git hash-object $file`);
    $LOGGER->debug("$cmd => $hash");
    return $hash;
}

sub git_find_file($) {
    my ($file) = @_;

    my $base = basename($file);

    chomp(my $list = `git ls-files | grep /$base`);
    my @poss = split /\n/, $list;
    return $poss[0] if scalar(@poss) == 1;

    my @exact = grep {basename($_) eq $base} @poss;
    return $exact[0] if scalar(@exact) == 1;

    # Look for a match that adds a suffix because desdist.pl is
    # installed as desdist.
    my @approx = grep {basename($_) =~ m/^$base\.\w+$/} @poss;
    return $approx[0] if scalar(@approx) == 1;

    return $file;
}

sub find_in_path($) {
    my ($file) = @_;
    my @path = split(":", $ENV{PATH});
    foreach my $d (@path) {
        if (-f "$d/$file") {
            $LOGGER->debug("find_in_path: $file -> $d/$file");
            return "$d/$file";
        }
    }
    return $file;
}

# --------------------------------------------

sub check_tree($$$) {
    my ($tree, $hash, $filename) = @_;


    my $cmd = "git ls-tree -r --full-name $tree";
    $LOGGER->debug($cmd);
    open my $ls_tree, '-|', $cmd,
        or $LOGGER->logconfess("Couldn't open pipe to $cmd: $!");

    while (my $line = <$ls_tree>) {
        chomp($line);
        if ($line !~ /\A[0-7]{6} (\S+) (\S+)\t(\S+)/) {
            die "unexpected git-ls-tree output: '$_'";
        }
        my $ctype     = $1; # "blob"
        my $chash     = $2;
        my $cfilename = $3;
        if ($chash eq $hash) {
            if ($cfilename =~ m@/$filename$@) {
                $LOGGER->debug("$cfilename $chash == $hash");
            }
            return $cfilename;
        }
        if ($cfilename =~ m@/$filename$@) {
            $LOGGER->debug("$cfilename $chash != $hash");
        }
    }
    close($ls_tree)
        or $LOGGER->error("Couldn't close pipe to $cmd: $!");

    return;
}

sub find_commit($@) {
    my $file = shift(@_);
    my $base = basename($file);
    my $hash = git_hash($file);

    if (!git_present_in_repo($hash)) {
        return;
    }

    my $git_loc = git_find_file($file);

    my $cmd = 'git log --pretty=format:"%T %h %ce %ci %s" ' . $git_loc;
    $LOGGER->debug($cmd);
    open my $log, '-|', $cmd,
        or $LOGGER->logconfess("Couldn't open pipe to $cmd: $!");

    my @retval;
    while (my $line = <$log>) {
        chomp($line);
        my ($tree, $commit, $user, $date, $time, $tz, $subject) = split " ", $line, 7;
        my $path = check_tree($tree, $hash, $base);
        if ($path) {
            $user =~ s/\@deshaw.com$//;
            $date = join(' ', $date, $time, $tz);
            @retval = ($path, $commit, $user, $date, $subject);
        }
        elsif (@retval) {
            # Return after we find the first commit which doesn't match
            return @retval;
        }
    }

    close($log)
        or $LOGGER->error("Couldn't close pipe to $cmd: $!");
}

# --------------------------------------------

main();

# --------------------------------------------
