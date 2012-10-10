#!/usr/local/bin/perl -w
# $Header: /u/yuanc/testbed/PL/RCS/photos.pl,v 1.2 2003/09/08 14:49:24 yuanc Exp $
#
use strict;
use Getopt::Std;
use CGI::Pretty qw( :standard -no_debug );

our($opt_d, $opt_v, $opt_p, $opt_r, $opt_l);
getopts("dlprv") or die;
my $debug = defined($opt_d);
my $verbose = defined($opt_v);
my $do_pics = defined($opt_p);
my $do_list = defined($opt_l);
my $rotate = defined($opt_r);
sub verbose ( $ ) {
    my ($msg) = @_;
    if ($verbose) {
	print $msg;
    }
}

sub run_cmd ( $ ) {
    my ($cmd) = @_;
    verbose "running $cmd\n";
    if ($debug) {
	print "Would: $cmd\n";
    } else {
	system($cmd) == 0
	  or die "$cmd failed: $? $| $!";
    }
}

#
# manipulating pictures
#
sub run_pnm_cmd_on_jpeg ( $$$;$ ) {
    my ($from_file, $to_dir, $cmd, $comp) = @_;
    # cjpeg defaults to -quality 75 (75% of original)
    $comp = "" unless(defined($comp));
    if ( ! -d $to_dir ) {
	verbose "$to_dir does not exist, making it\n";
	if ($debug) {
	    print "Would: mkdir $to_dir\n";
	} else {
	    mkdir $to_dir;
	    chmod 0755, $to_dir;
	}
    }
    $from_file = "\"$from_file\"";
    chomp(my $basename = `basename $from_file`);
    my $to_file = $to_dir . "/" . $basename;
    run_cmd("djpeg $from_file | $cmd | cjpeg $comp > \"$to_file\"");
    chmod 0644, $to_file;
}

sub scale_jpeg ( $$;$$ ) {
    my ($from_file, $to_dir, $scale, $comp) = @_;
    $scale = "0.4" unless(defined($scale));
    run_pnm_cmd_on_jpeg($from_file, $to_dir, "pnmscale $scale", $comp);
}

sub thumb ( $$ ) {
    my ($from, $to_dir) = @_;
    scale_jpeg($from,$to_dir,"-width 100");
}

sub regular ( $$ ) {
    my ($from, $to_dir) = @_;
    scale_jpeg($from,$to_dir);
}

sub rotccw_jpeg ( $$ ) {
    my ($from, $to_dir) = @_;
    run_pnm_cmd_on_jpeg($from, $to_dir, "pnmflip -ccw");
}

sub rotcw_jpeg ( $$ ) {
    my ($from, $to_dir) = @_;
    run_pnm_cmd_on_jpeg($from, $to_dir, "pnmflip -cw");
}

#
# MAIN
#

if ($rotate) {
    my $dir = shift(@ARGV);
    foreach my $file (@ARGV) {
	rotcw_jpeg ($file, $dir);
    }
    exit 0;
}

if (scalar(@ARGV) != 1) {
    die "Usage: $0 <dir>";
}
my ($dir) = @ARGV;

my $local_dir = "/u/yuanc/.www/$dir";
my $web_dir = "http://www/~yuanc/$dir";

#
# moving pictures
#
# mkdir $local_dir . "/full";
# mkdir $local_dir . "/rot";
# mv * full;
# "/usr/bin/ls -1 $local_dir/full/*r1* | sed 's/_r1.jpg/.JPG/' | /u/yuanc/bin/apply -dv 'mv %s $local_dir . /rot'"
#
# getting pictures
#
my $full_dir = $local_dir . "/full";
opendir(DIR, $full_dir) || die "can't opendir $full_dir: $!";
my @pics = grep {
                  m/^[^\.].*\.jp(e|)g$/i && -f "$full_dir/$_" 
	        } readdir(DIR);
closedir(DIR);

if ($do_list) {
    if (!$debug) {
	open(LIST, ">$local_dir/list") or die "Can't write to $local_dir/list";
    }
}
foreach my $pic (@pics) {
    if ($do_list) {
	if ($debug) {
	    verbose("would write to list: $pic\n");
	} else {
	    verbose("writing to list: $pic\n");
	    print LIST $pic . "\n";
	}
    }
    if ($do_pics) {
	thumb  ($pic, $local_dir . "/thumb");
	regular($pic, $local_dir ."/reg");
    }
}
if ($do_list) {
    if (!$debug) {
	close(LIST);
    }
    verbose("doing chmod\n");
    chmod(0644, $local_dir . "/list"); 
}

