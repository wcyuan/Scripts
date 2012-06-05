#!/usr/local/bin/perl -w
#############################################################
###
### prints grey code for X bits
### i.e. all binary numbers in an order such that you only flip one bit
### between each number
###
use strict;
use Getopt::Std;

use vars qw($total_bits $debug $opt_d $base @array);
sub initialize_array ($$);
sub      print_array ($);
sub        grey_code ($$$);

getopts("d") || die "usage: $0 {bits} {base}\n";
$debug = defined($opt_d);
$base       = @ARGV > 1 ? $ARGV[1]     : 2;
$total_bits = @ARGV > 0 ? $ARGV[0] - 1 : 3;

&initialize_array ($total_bits, 0);
&grey_code ($total_bits, $base, 1);

exit 0;

sub grey_code ($$$) {
  my ($bits, $base, $parity) = @_;
  my ($ii, $next_parity);
  if ($bits < 0) {
    &print_array ($total_bits, @array);
    return;
  }
  print "grey_code $bits, $base, $parity\n"
    if ($debug);

  # either of these works
  $next_parity = $array[$bits-1] ? -1 : 1;
  $next_parity = $base % 2 ? $parity : 1;

  for ($ii = 1; $ii < $base; $ii++) {
    &grey_code ($bits-1, $base, $next_parity);
    $array[$bits] += $parity;
    $next_parity *= -1;
  }
  &grey_code ($bits-1, $base, $next_parity);
}

sub initialize_array ($$) {
  my ($bits, $value) = @_;
  my $ii;
  for ($ii = 0; $ii <= $bits; $ii++) {
    $array[$ii] = $value;
  }
}

sub print_array ($) {
  my ($bits) = @_;
  my $ii;
  for ($ii = $bits; $ii >= 0; $ii--) {
    printf ("%d", $array[$ii]);
  }
  printf ("\n");
}
