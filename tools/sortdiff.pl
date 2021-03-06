#!/usr/local/bin/perl -w
#
# sortdiff.pl
# @desc:  diff two files unordered (sort them first).
#
# Conan Yuan, 20050408
#

=head1 NAME

sortdiff.pl - diff two files unordered (sort them first).

=head1 SYNOPSIS

  sortdiff.pl [options] <file1> <file2>

  Options:
    --col 1=1,2..5 --col 2=1,5..8
                      compare columns 1, 2, 3, 4, 5 of the first file
                      with columns 1, 5, 6, 7, 8 of the second file
                      column numbers are zero indexed
    --debug           create temporary files, but don't run the diff command
    --uniq            remove duplicate lines
    --leave           leave the temporary files that were created
    --join            run join on the sorted files instead of diff
    --help, -?        shows brief help message
    --perldoc         shows full documentation
    other options     passed onto diff

  See also Getopt::Long for complete standard options list.

=head1 ARGUMENTS

=over

=item I<file1>

the first file.  "-" indicates stdin.

Note that the files are opened with perl open, so it's easy to pass a command instead of a file, like this:

sortdiff "gzcat file1.gz |" "bzcat file2.bz2 |"

=item I<file2>

the second file.  "-" indicates stdin.  If both files are stdin, the script will
probably hang (rather than die with an error).

=back

=head1 OPTIONS

=over

=item I<--col>

a hash (a=b pairs) indicating which columns of each file to compare

=item I<--uniq>

remove duplicate lines

=item I<--leave>

leave the temporary files that were created

=item I<--join>

run join on the sorted files instead of running diff

=item I<--debug>

create temporary files, but don't run the diff command

=item I<--help>

Print a brief help message and exits.

=item I<--perldoc>

Prints the perldoc page and exits.

=item I<other options>

are passed onto diff

=back

=head1 DESCRIPTION

sort files, then diff them.

=cut

use strict;
use Pod::Usage;
use File::Basename;
use File::Temp qw(tempfile);

use Getopt::Long qw(:config pass_through no_auto_abbrev);
use Log::Log4perl qw(:levels);

# ---------------------------------------------------------------

# default values
my $nfiles = 2;
my %file;
Log::Log4perl->easy_init($ERROR);
my $logger = Log::Log4perl->get_logger();

# parse command-line options
GetOptions( "col=s"    => \my %col,
            "uniq!"    => \my $uniq,
            "debug!"   => \my $debug,
            "leave!"   => \my $leave_files,
            "join!"    => \my $do_join,
            "verbose|v" => sub { $logger->level($DEBUG) },
            "cmd!"     => \my $is_cmd,

            # Why would you want nosort mode?  This script is also
            # useful for comparing the output of two functions without
            # having to save the output to files first, and in that
            # case you might not want to sort the output before
            # comparing it.
            "nosort!"  => \my $nosort,
          )
    or pod2usage();

# parse script arguments
pod2usage("Wrong number of arguments") unless @ARGV >= $nfiles;

# Suppose we want to pass the option -v to the subcommand (diff or
# join).  We don't want -v to be consumed by the GetOptions above.  So
# we add '--' before the '-v' to tell GetOptions to stop reading
# options, e.g.
#
#   sortdiff --join -- -v 2  file1.txt file2.txt
#
# That works, but it leaves the '--' in ARGV.  So we have to
# consume it here.
shift(@ARGV) if $ARGV[0] eq '--';

# ---------------------------------------------------------------
# Create temporary filenames
#

my $cmd_basename = basename($0);
# Pop two arguments off the end of @ARGV.  Earlier arguments will be
# passed into the diff command.  Since we're popping, we get the files
# in reverse order.
for (my $ii = $nfiles; $ii > 0; $ii--) {
    $file{$ii}{name} = pop(@ARGV);
    $file{$ii}{temp} = (tempfile())[1];
}

for (my $ii = 1; $ii <= $nfiles; $ii++) {
    if ($ii > 1) {
        if (-d $file{$ii}{name}) {
            # After the first file, the later files can just be
            # directories and we'll assume the same basename as the
            # first file.
            $file{$ii}{name} .= basename($file{1}{name});
        }
    }
    $logger->debug("file $ii: '$file{$ii}{name}' -> $file{$ii}{temp}");
}

foreach my $fileno (keys %col) {
    if (!defined($file{$fileno})) {
	pod2usage("Invalid file id $fileno ($col{$fileno})");
    }
    $file{$fileno}{col} = $col{$fileno};
}

# ---------------------------------------------------------------
# Read input files, output to temp files
#

foreach my $fileno (keys %file) {
    my $infd;
    $logger->debug("Reading file $fileno: '$file{$fileno}{name}'");
    open($infd, $file{$fileno}{name})
        or $logger->logconfess("Can't open $file{$fileno}{name}: $? $! $@");
    my @lines;
    my %uniqlines;
    while(<$infd>) {
	my $line = $_;
	if (defined($file{$fileno}{col})) {
	    my @fields = split(' ', $line);
            # Eval the argument so that 2..5 gets translated into (2, 3, 4, 5)
	    my @specified = map {eval $_} split(',', $file{$fileno}{col});
	    $line = join(' ', map {$_//""} @fields[@specified]) . "\n";
	}
	if (!$uniq || !exists($uniqlines{$_})) {
	    push(@lines, $line);
	    $uniqlines{$line} = 1;
	}
    }
    # what if it's stdin?
    close($infd);
    my $outfd;
    open($outfd, ">" . $file{$fileno}{temp})
        or $logger->logconfess("Can't overwrite $file{$fileno}{temp}: $! $@ ?");
    if ($nosort) {
        print $outfd @lines;
    } else {
        print $outfd sort(@lines);
    }
    close($outfd)
        or $logger->logconfess("Can't close $file{$fileno}{temp}: $? $! $@");
}

# ---------------------------------------------------------------
# Run the diff command
#

my $cmd = join(" ", "diff", @ARGV, $file{1}{temp},  $file{2}{temp});
if ($do_join) {
    $cmd = join(" ", "join", @ARGV, $file{1}{temp},  $file{2}{temp});
}
if ($debug) {
    $logger->debug("Not running '$cmd'");
} else {
    $logger->info("Running '$cmd'");
    system($cmd);
}

# ---------------------------------------------------------------
# Remove temp files
#

foreach my $fileno (keys %file) {
    if ($leave_files) {
	$logger->warn("Leaving file $file{$fileno}{temp}");
    } else {
	unlink($file{$fileno}{temp})
            or warning("Can't remove $file{$fileno}{temp}: $? $! $@");
    }
}

# ----------------------

__END__

=head1 AUTHOR

 Conan Yuan

=cut

