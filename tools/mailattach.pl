#!/usr/local/bin/perl -w
#
# mailattach.pl
# @desc:  Mail files as attachments
#
# Conan Yuan, 20090514
#

=head1 NAME

mailattach.pl - Mail files as attachments

=head1 SYNOPSIS

  mailattach.pl [options] <mailto> <files>

  Options:
    --attach          file to attach
    --mailto          recipients
    --help, -?        shows brief help message
    --perldoc         shows full documentation

  See also Getopt::Long for complete standard options list.

=head1 ARGUMENTS

=over

=item I<mailto>

who to mail to

=item I<files>

the files to attach

=back

=head1 OPTIONS

=over 4

=item I<--attach>

files to attach

=item I<--mailto>

the recipients of the mail

=item I<--help>

Print a brief help message and exit.

=item I<--perldoc>

Print the perldoc page and exit.

=back

=head1 DESCRIPTION

Complete description.

=cut

use strict;
use warnings 'all';
use Pod::Usage;
use MIME::Lite;

use Getopt::Long;
use Log::Log4perl qw(:levels);

# ----------------------

# Default values
my @attach = ();
my $user = getpwuid($<);
my @mailto = ($user);
my @save_args = @ARGV;
Log::Log4perl->easy_init($ERROR);
my $logger = Log::Log4perl->get_logger();

# Parse any command-line options
GetOptions( "attach=s"  => \@attach,
            "mailto=s"  => \@mailto,
            "verbose|v" => sub { $logger->level($DEBUG) },
            "no_write"  => \my $no_write,
          )
    or pod2usage();

push(@mailto, shift @ARGV)
    if (scalar(@ARGV) > 0);
push(@attach, @ARGV);

# ----------------------

if (scalar(@mailto) == 0) {
    print "No recipients, exiting\n";
    exit;
}
if (scalar(@attach) == 0) {
    print "Nothing to send, exiting\n";
    exit;
}

my $msg = MIME::Lite->new(From => $user,
			  To => join(',', @mailto),
			  Subject => $0 . " " . join(' ', @save_args),
			  Type => 'multipart/mixed');

foreach my $file (@attach) {
    $msg->attach(Type => 'text/plain',
		 Path => $file,
		 Disposition => 'attachment');
}

$logger->debug($msg->as_string());

if (!$no_write) {
    $msg->send();
}


# ----------------------

__END__

=head1 AUTHOR

 Conan Yuan

=cut

