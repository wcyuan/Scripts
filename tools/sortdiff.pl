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
    --col 1=1,2 --col 2=1,5
                      compare the first and second columns of the first file
                      with the first and fifth columns of the second file
                      column numbers are zero indexed
    --debug           create temporary files, but don't run the diff command
    --uniq            remove duplicate lines
    --leave           leave the temporary files that were created
    --help, -?        shows brief help message
    --perldoc         shows full documentation
    other options     passed onto diff

  See also Getopt::Long for complete standard options list.

=head1 ARGUMENTS

=over

=item I<file1>

the first file.  "-" indicates stdin.

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
            "verbose|v" => sub { $logger->level($DEBUG) },
            "cmd!"     => \my $is_cmd,
          )
    or pod2usage();

# parse script arguments
pod2usage("Wrong number of arguments") unless @ARGV >= $nfiles;

# ---------------------------------------------------------------
# Create temporary filenames
#

my $cmd_basename = basename($0);
# Pop two arguments off the end of @ARGV.  Earlier arguments will be
# passed into the diff command.  Since we're popping, we get the files
# in reverse order.
for (my $ii = $nfiles; $ii > 0; $ii--) {
    $file{$ii}{name} = pop(@ARGV);
    $file{$ii}{temp} = "/tmp/$cmd_basename.$ii.$$";
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
	    my @specified = split(',', $file{$fileno}{col});
	    $line = join(' ', @fields[@specified]) . "\n";
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
    print $outfd sort(@lines);
    close($outfd)
        or $logger->logconfess("Can't close $file{$fileno}{temp}: $? $! $@");
}

# ---------------------------------------------------------------
# Run the diff command
#

my $cmd = join(" ", "diff", @ARGV, $file{1}{temp},  $file{2}{temp});
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

