#!/usr/local/bin/perl -w
#

=head1 NAME

template.pl - description

=head1 SYNOPSIS

  template.pl [options]

  Options:
    --help, -?        shows brief help message
    --perldoc         shows full documentation

=head1 ARGUMENTS

=over

=item I<--arg1>

description

=back

=head1 OPTIONS

=over 4

=item I<--opt1>

description

=back

=head1 DESCRIPTION

=cut

use strict;
use warnings 'all';
use Pod::Usage;

use Getopt::Long;
use Log::Log4perl qw(:levels);

# ----------------------

Log::Log4perl->easy_init($ERROR);
my $LOGGER = Log::Log4perl->get_logger();

# ----------------------

sub main() {
    getopts();
}

sub getopts() {
    # parse command-line options
    GetOptions("verbose"      => sub { $LOGGER->level($DEBUG) },
               "log_level=s"  => sub { $LOGGER->level($_[1]) },
              )
        or pod2usage();

    # parse script arguments
    pod2usage("Wrong number of arguments") unless @ARGV == 0;

    return;
}

# ----------------------

main();

# ----------------------

__END__

=head1 AUTHOR

 Conan Yuan

=cut

