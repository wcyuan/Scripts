#!/usr/bin/env perl
#
# shorten.pl
# @desc:  shorten lines
#
# Conan Yuan, 20110105
#

=head1 NAME

shorten.pl - shorten lines

=head1 SYNOPSIS

  shorten.pl [options] <length>

  Options:
    --help, -?        shows brief help message
    --perldoc         shows full documentation

  See also Getopt::Long for complete standard options list.

=head1 ARGUMENTS

=over

=item I<length>


=back

=head1 OPTIONS

=over 4

=item I<--help>

Print a brief help message and exit.

=item I<--perldoc>

Print the perldoc page and exit.

=back

=head1 DESCRIPTION

shorten lines

=cut

use strict;
use warnings 'all';

use Pod::Usage;
use Getopt::Long;
use Log::Log4perl qw(:levels);
use Scalar::Util qw(looks_like_number);
use Text::Tabs qw(expand);

# ----------------------

# Default values
my $OFFSET = 0;
Log::Log4perl->easy_init($ERROR);
my $logger = Log::Log4perl->get_logger();

# Parse any command-line options
GetOptions( "offset|o=i" => \$OFFSET,
            "width|w=i"  => \my $WIDTH,
            "verbose|v!" => sub { $logger->level($DEBUG) },
          )
    or pod2usage();

if (!defined($WIDTH) &&
    scalar(@ARGV) > 0 &&
    ! -f $ARGV[0] &&
    looks_like_number($ARGV[0]))
{
    $logger->debug("Taking WIDTH from first argument");
    $WIDTH = shift(@ARGV);
}

if (!defined($WIDTH))
{
    $logger->debug("Trying to get width from Term::ReadKey");
    eval {
        require Term::ReadKey;
        my ($wchar, $hchar, $wpixels, $hpixels) = Term::ReadKey::GetTerminalSize();
        $WIDTH = $wchar;
    };
}

if (!defined($WIDTH))
{
    $logger->debug("Trying to get width from stty size");
    eval {
        # This is supposed to work on linux, but it doesn't seem to.
        # Could also try to parse stty -a.
        chomp(my $tty_size = `stty size`);
        $WIDTH = (split(' ', $tty_size))[1];
    }
}

if (!defined($WIDTH))
{
    $logger->debug("Defaulting to hard coded width");
    $WIDTH = 139;
}

my @FILES = @ARGV;

$logger->debug("WIDTH  = $WIDTH");
$logger->debug("OFFSET = $OFFSET");
$logger->debug("FILES  = " . join(', ', @FILES));

# ----------------------

sub shorten($) {
    my ($line) = @_;
    # expand tabs.  otherwise substr sees the tab as a
    # single character, and won't shorten the line enough.
    $line = expand($line);
    $line = substr($line, $OFFSET, $WIDTH);
    # trim trailing whitespace
    $line =~ s/\s+$//g;
    return $line;
}

sub main() {
    if (scalar(@FILES) == 0) {
        while (my $line = <>) {
            chomp($line);
            print shorten($line) . "\n";
        }
    }
    else {
        foreach my $f (@FILES) {
            my $fd;
            open($fd, $f, "r");
            if (!$fd) {
                $logger->error("Can't open $f: $? $! $@");
                next;
            }
            while (my $line = <$fd>) {
                chomp($line);
                print shorten($line) . "\n";
            }
            close($fd)
                or $logger->error("Can't close $f: $? $! $@");
        }
    }
}

# ----------------------

main();

# ----------------------

__END__

=head1 AUTHOR

 Conan Yuan

=cut

