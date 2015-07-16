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
use Scalar::Util qw(looks_like_number);
use Text::Tabs qw(expand);
use Term::ANSIColor qw(:constants);

# ------------------------------------------------------------------------------

package Logger;

#
# Use this simple Logger class instead of Log::Log4perl because
# Log::Log4perl doesn't seem to be installed by default on cygwin.
#

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
    $self->{level} = $level;
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

# ----------------------

package main;

# Default values
my $LOGGER = new Logger();

sub getopt() {
  # Parse any command-line options
  GetOptions( "offset|o=i" => \my $offset,
              "width|w=i"  => \my $width,
              "verbose|v!" => sub { $LOGGER->level('DEBUG') },
              "pattern|p=s" => \my $pattern,
    )
    or pod2usage();

  if (!defined($width) &&
      scalar(@ARGV) > 0 &&
      ! -f $ARGV[0] &&
      looks_like_number($ARGV[0]))
  {
    $LOGGER->debug("Taking WIDTH from first argument");
    $width = shift(@ARGV);
  }

  if (!defined($width))
  {
    $LOGGER->debug("Trying to get width from Term::ReadKey");
    eval {
      require Term::ReadKey;
      my ($wchar, $hchar, $wpixels, $hpixels) = Term::ReadKey::GetTerminalSize();
      $width = $wchar;
    };
  }

  if (!defined($width))
  {
    $LOGGER->debug("Trying to get width from stty size");
    eval {
      # This is supposed to work on linux, but it doesn't seem to.
      # Could also try to parse stty -a.
      chomp(my $tty_size = `stty size`);
      $width = (split(' ', $tty_size))[1];
    }
  }

  if (!defined($width))
  {
    $LOGGER->debug("Defaulting to hard coded width");
    $width = 139;
  }

  my @files = @ARGV;

  $LOGGER->debug("WIDTH  = $width");
  $LOGGER->debug("OFFSET = " . ($offset // "undefined"));
  $LOGGER->debug("PATTERN = ". ($pattern // "undefined"));
  $LOGGER->debug("FILES  = " . join(', ', @files));

  return (\@files, $width, $offset, $pattern);
}

# ----------------------

sub shorten($$$$) {
    my ($line, $offset, $width, $pattern) = @_;
    # expand tabs.  otherwise substr sees the tab as a
    # single character, and won't shorten the line enough.
    $line = expand($line);

    if (!defined($offset)) {
      if (defined($pattern)) {
        $offset = index($line, $pattern);
        if ($offset > 10) {
          $offset -= 10;
        } elsif ($offset >= 0) {
          $offset = 0;
        }
      }
      if (!defined($offset) || $offset < 0) {
        $offset = 0;
      }
    }

    $line = substr($line, $offset, $width);
    if (defined($pattern)) {
      my $boldred = BOLD RED;
      my $reset = RESET;
      $line =~ s/($pattern)/${boldred}${1}${reset}/g;
    }
    # trim trailing whitespace
    $line =~ s/\s+$//g;
    return $line;
}

sub main() {
    my ($files, $width, $offset, $pattern) = getopt();
    if (scalar(@$files) == 0) {
        while (my $line = <>) {
            chomp($line);
            print shorten($line, $offset, $width, $pattern) . "\n";
        }
    }
    else {
        foreach my $f (@$files) {
            my $fd;
            open($fd, $f, "r");
            if (!$fd) {
                $LOGGER->error("Can't open $f: $? $! $@");
                next;
            }
            while (my $line = <$fd>) {
                chomp($line);
                print shorten($line, $offset, $width, $pattern) . "\n";
            }
            close($fd)
                or $LOGGER->error("Can't close $f: $? $! $@");
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
