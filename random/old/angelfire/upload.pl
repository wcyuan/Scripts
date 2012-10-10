#!/usr/local/bin/perl -w
# $Header: /u/yuanc/testbed/PL/angelfire/RCS/upload.pl,v 1.4 2003/09/07 02:11:59 yuanc Exp $

use strict;
use Net::FTP;
use Getopt::Std;
use CGI::Pretty qw( :html3 -no_debug );

use vars qw($opt_d $opt_v $opt_u $opt_p $opt_l);
getopts("dlpuv") or die;
my $debug = defined($opt_d);
my $verbose = defined($opt_v);
my $upload_pics = defined($opt_u);
my $upload_page = defined($opt_p);
my $use_local_page = defined($opt_l);

my $USAGE = "$0 -dvupl <album>";

sub verbose ( $ ) {
    my ($msg) = @_;
    if ($verbose) {
	print $msg;
    }
}

my $MAIN_DIR = "/u/yuanc/testbed/PL/angelfire";

{
    my %locs = ();
    sub read_locs () {
	open(LOCATIONS, $MAIN_DIR . "/locations")
	  or die "Can't open $MAIN_DIR/locations: $? $!";
	while(<LOCATIONS>) {
	    next if /^(\s*)(\#.*|)$/;
	    my ($id, $http, $ftp, $login, $password, $dir) = split;
	    $locs{$id} = {
			  "http" => $http,
			  "ftp" => $ftp,
			  "user" => $login,
			  "pass" => $password,
			  "dir" => $dir,
			 };
	}
	close(LOCATIONS);
    }

    sub get_loc_info ( $% ) {
	my $id = shift @_;
	# vals overrides the location info
	my %vals = @_;
	my $loc_info;
	if (defined($locs{$id})) {
	    $loc_info = $locs{$id};
	}
	my %defaults = (
			"user" => $id . "/yuan_photos",
			"pass" => "photos",
			"ftp" => "ftp.angelfire.com",
			"dir" => "images",
			"http" => "www.angelfire.com",
			"type" => "I",
			"scale" => "web",
		       );
	my $retval = {};
	foreach my $var (keys(%defaults)) {
	    if (defined($vals{$var})) {
		$retval->{$var} = $vals{$var};
	    } elsif (defined($loc_info->{$var})) {
		$retval->{$var} = $loc_info->{$var};
	    } else {
		$retval->{$var} = $defaults{$var};
	    }
	}
	return $retval;
    }
}

# indicates the way that angelfire represents a user's homepage --
# they just append it to the base url
# rather than, say, using a tilde, i.e. base_url/~username
sub get_homepage ( $$ ) {
    my ($url, $user) = @_;
    return $url . "/" . $user;
}

{
    my ($ftp, %curr);
    sub set_url ( $$$ ) {
	my ($url, $user, $pass) = @_;
	my %spec = (
		    "url" => $url, 
		    "user" => $user, 
		    );
	my $reopen = 0;
	foreach my $var ("url", "user") {
	    if (!defined($curr{$var}) || ($spec{$var} ne $curr{$var})) {
		$reopen = 1;
	    }
	}
	if (!defined($ftp) || $reopen) {
	    verbose "opening $user:$pass\@$url\n";
	    close_ftp();
	    if (!$debug) {
		$ftp = Net::FTP->new($url) or die "Cannot connect to $url: $@";
		$ftp->login($user,$pass) 
		    or die "Cannot login to $url as $user:$pass ", $ftp->message();
	    }
	    foreach my $var (keys %curr) {
		$curr{$var} = undef;
	    }
	    $curr{url} = $url;
	    $curr{user} = $user;
	}
    }

    sub set_ftp_mode ( $$ ) {
	my ($var, $val) = @_;
	if (!defined($curr{$var}) || $val ne $curr{$var}) {
	    verbose "changing $var to $val\n";
	    if (!$debug) {
		if ($var eq "dir") {
		    $val = "/" . $val;
		    if (!$ftp->cwd($val)) {
			$ftp->mkdir($val) or goto ERROR;
			$ftp->cwd($val) or goto ERROR;
		    }
		}
		elsif ($var eq "type") {
		    $ftp->type($val) or goto ERROR;
		}
		else {
		    die "Unknown ftp mode $var";
		}
	    }
	    $curr{$var} = $val;
	}
	return;
      ERROR:
	die "Cannot change $var to $val ", $ftp->message();
    }

    sub put_file( $$$$$$ ) {
	my ($user, $pass, $url, $dir, $type, $file) = @_;
	set_url($url, $user, $pass);
	set_ftp_mode("dir", $dir);
	set_ftp_mode("type", $type);
	chomp(my $cdir = `pwd`);
	$file = "\"$file\"";
	chomp(my $ldir = `dirname $file`);
	chomp(my $basename = `basename $file`);
	verbose "putting $file to $user:$pass\@" 
	      . get_homepage($url,$user) 
	      . "/$dir/$basename\n";
	if (!$debug) {
	    chdir($ldir) or die "Can't change to $ldir";
	    $ftp->put($basename) or die "Can't put $file";
	    chdir($cdir) or die "Can't change to $cdir";
	}
    }

    sub run_cmd ( $ ) {
	my ($cmd) = @_;
	system($cmd) == 0
	    or die "$cmd failed: $? $| $!";
    }

    sub scale_jpeg ( $;$$ ) {
	my ($file, $scale, $comp) = @_;
	$file = "\"$file\"";
	chomp(my $basename = `basename $file`);
	my $temp_file = "/tmp/" . $basename;
	$scale = "0.4" unless(defined($scale));
	# cjpeg defaults to -quality 75 (75% of original)
	$comp = "" unless(defined($comp));
	run_cmd("djpeg $file | pnmscale $scale | cjpeg $comp > \"$temp_file\"");
	return $temp_file;
    }

    sub put_file_by_id( $$% ) {
	my ($id, $file, %vars) = @_;
	my $info_ref = get_loc_info($id, %vars);
	if ($info_ref->{scale} eq "web") {
	    $file = scale_jpeg($file);
	}
	elsif ($info_ref->{scale} eq "thumb") {
	    $file = scale_jpeg($file,"-width 100");
	}
	put_file($info_ref->{user}, 
		 $info_ref->{pass}, 
		 $info_ref->{ftp},
		 $info_ref->{dir},
		 $info_ref->{type},
		 $file);
    }

    sub close_ftp () {
	if (defined($ftp)) {
	    $ftp->quit;
	}
    }
}

sub get_loc_url ( $$$% ) {
    my ($id, $use_local_page, $local_dir, %vars) = @_;
    if ($use_local_page) {
	# XXX this depends....
	return "N:" . $local_dir . "/"; 
    } else {
	my $info_ref = get_loc_info($id, %vars);
	return "http://" 
	     . get_homepage($info_ref->{http},$info_ref->{user}) 
	     . "/" . $info_ref->{dir} . "/";
    }
}

sub get_album_info ( $ ) {
    my ($a_info_file) = @_;
    open(ALBUM_INFO, $a_info_file) or die "Can't open $a_info_file: $? $!";
    my $mode;
    my $local_dir;
    my $simple_html;
    my $simple_html_loc;
    my $script_html;
    my $script_html_loc;
    my $page_title = "";
    my @pics;
    my $loc_id;
    my $pic_uploaded = 0;
    while(<ALBUM_INFO>) {
	chomp(my $line = $_);
	if ($line =~ m/^\s*(\#.*|)$/) {
	    next;
	}
	if ($line =~/^=(.*)$/) {
	    if ($1 eq "done") {
		$pic_uploaded = 1;
	    } elsif ($1 eq "notdone") {
		$pic_uploaded = 0;
	    } else {
		$mode = $1;
		verbose("setting mode to $mode\n");
	    }
	}
	elsif (defined($mode)) {
	    if ($mode =~ m/^local_dir\s*$/) {
		# local_dir needs to include the trailing slash
		# otherwise, it's considered a prefix.  
		# it ought to be the full path
		$local_dir = $line;
	    }
	    elsif ($mode =~ /^simple_html\s*$/) {
		if (!defined($loc_id)) {
		    die "Undefined location for $mode";
		}
		$simple_html = $line;
		$simple_html_loc = $loc_id;
	    }
	    elsif ($mode =~ /^script_html\s*$/) {
		if (!defined($loc_id)) {
		    die "Undefined location for $mode";
		}
		$script_html = $line;
		$script_html_loc = $loc_id;
	    }
	    elsif ($mode =~ /^title\s*$/) {
		$page_title = $line;
	    }
	    elsif ($mode =~ /^remote_loc$/) {
		$loc_id = $line;
	    }
	    elsif ($mode =~ /^pics\s*$/) {
		#my ($loc_id, $file, $title) = split(/\t/,$line);
		my ($file) = split(/\t/,$line);
		my $title = "";
		if (!defined($loc_id)) {
		    die "Undefined location for pic $file";
		}
		if (!defined($local_dir)) {
		    die "Undefined local dir for pic $file";
		}
		push(@pics, [$loc_id, $file, $local_dir, $title, $pic_uploaded]);
	    }
	    else {
		die "Unrecognized mode $mode";
	    }
	    if ($mode ne "pics") {
		verbose("setting $mode to $line\n");
	    }
	}
    }
    close(ALBUM_INFO) or die "Can't close $a_info_file: $? $!";
    return ($page_title, \@pics, $simple_html, $simple_html_loc, $script_html, $script_html_loc);
}

sub upload_pics ( $;$ ) {
    my ($pics, $dir) = @_;
    if (!defined($dir)) {
	# before using dir, need to update pic_url
	$dir = "";
    }
    $dir .= "/images/";
    foreach my $pic_info (@$pics) {
	my ($loc_id, $file, $local_dir, $title, $uploaded) = @$pic_info;
	next if ($uploaded);
	foreach my $type ("reg", "thumb") {
	    put_file_by_id($loc_id, $local_dir . $file, "scale"=>$type, "dir"=>$dir . $type);
	}
    }
}

sub links ( $ ) {
    my ($q) = @_;
    return $q->p(
		 $q->a({href=>"http://www.angelfire.com/folk/yuan_photos/"},
		       "more photos"),
		 " / ",
		 $q->a({href=>"http://www.geocities.com/wcyuan/"},
		       "homepage"),
		 );
}

sub page_style () {
    my $style=<<END_STYLE;	
    body {
	font-family: "comic sans ms", sans-serif;
    }
    A {
	text-decoration: none;
    }
    A:active {
        color: yellow;
    }
    A:hover {
        color: red;
    }
    A:visited {
        color: purple;
    }
END_STYLE
    return $style;
}

sub output_simple ( $$$$$$ ) {
    my ($output_html, $html_loc, $use_local_page, $upload_page, $page_title, $pics) = @_;
    open(OUTPUT, ">$output_html") or die "Can't write to $output_html";
    my $q = new CGI::Pretty;
    print OUTPUT $q->start_html({title=>$page_title,
				 style=>{type=>"text/css",
					 code=>page_style(),
				        },
			        }
				);
    print OUTPUT links($q);
    print OUTPUT "<center>\n";
    foreach my $pic_info (@$pics) {
	my $pic_loc = pic_url($pic_info, "reg");
	print OUTPUT $q->p($q->a({href=>$pic_loc},
				 $q->img({src=>$pic_loc,
					  width=>"80%"})));
    }
    print OUTPUT "</center>\n";
    print OUTPUT links($q);
    print OUTPUT $q->end_html();
    close(OUTPUT);
    if ($upload_page) {
	put_file_by_id($html_loc, $output_html, "dir"=>"", "type"=>"A", "scale"=>"none");
    }
}

sub output_simple_thumbs ( $$$$$$ ) {
    my ($output_html, $html_loc, $use_local_page, $upload_page, $page_title, $pics) = @_;
    open(OUTPUT, ">$output_html") or die "Can't write to $output_html";
    my $q = new CGI::Pretty;
    print OUTPUT $q->start_html({title=>$page_title,
				 style=>{type=>"text/css",
					 code=>page_style(),
				        },
			        }
			       );
    print OUTPUT links($q);
    print OUTPUT "<center>\n";
    my @entries;
    foreach my $pic_info (@$pics) {
	my $reg = pic_url($pic_info, "reg");
	my $thumb = pic_url($pic_info, "thumb");
	push @entries, $q->a({href=>$reg},
			     $q->img({src=>$thumb}));
    }
    print OUTPUT $q->p(@entries);
    print OUTPUT "</center>\n";
    print OUTPUT links($q);
    print OUTPUT $q->end_html();
    close(OUTPUT);
    if ($upload_page) {
	put_file_by_id($html_loc, $output_html, "dir"=>"", "type"=>"A", "scale"=>"none");
    }
}

sub jscript_functions () {
    my $script=<<END_SCRIPT;
    function load()
    {
	old_browser.style.display="none";
	main.style.display="";
	thumb.style.display="";
    }

    function Select(pic)
    {
	mainpic.src=pic;
    }
END_SCRIPT
    return $script;
}

sub pic_url ( $;$$ ) {
    my ($pic_info, $type, $dir) = @_;
    if (!defined($type)) {
	$type = "reg";
    }
    my ($loc_id, $fn, $local_dir, $title) = @$pic_info;
    return get_loc_url($loc_id, $use_local_page, $local_dir, "dir"=>"images/" . $type) . $fn;
}

sub output_script ( $$$$$$$ ) {
    my ($output_html, $script_loc, $simple_html, $use_local_page, $upload_page, $page_title, $pics) = @_;
    open(OUTPUT, ">$output_html") or die "Can't write to $output_html";
    my $q = new CGI::Pretty;
    print OUTPUT $q->start_html({title=>$page_title,
				 style=>{type=>"text/css",
					 code=>page_style(),
				        },
				 script=>jscript_functions(),
				 onLoad=>"load()",
			        }
				);
    print OUTPUT links($q);
    print OUTPUT $q->div({id=>"old_browser",
			  style=>""},
			 "go ", 
			 $q->a({href=>"$simple_html"},"here"));
    print OUTPUT "<center>\n";
    print OUTPUT $q->table({id=>"main",
			    style=>"width: 100%; display: none;"},
			   $q->Tr({align=>"center"},
				  $q->td({valign=>"center"},
					 $q->img({src=>"",
						  alt=>"no photo found",
						  width=>"80%",
						  id=>"mainpic"}),
					 )));
    my @table_rows;
    foreach my $pic_info (@$pics) {
	my $pic_loc_thumb = pic_url($pic_info, "thumb");
	my $pic_loc_reg = pic_url($pic_info, "reg");
	push(@table_rows,
	     "<td><div><img src=\"$pic_loc_thumb\" onclick=Select(\"$pic_loc_reg\");></td></div>\n");
    }
    print OUTPUT $q->div({id=>"thumb",
			  style=>"display:none; "
			       . "width:100%; "
			       . "height:150; "
			       . "overflow-y:none; "
			       . "overflow-x:scroll;",
		         },
			 $q->table({style=>"overflow-x:scroll;"},
				   $q->Tr({height=>"120"},
					  @table_rows,)));
    print OUTPUT "</center>\n";
    print OUTPUT links($q);
    print OUTPUT $q->end_html();
    close(OUTPUT);
    if ($upload_page) {
	put_file_by_id($script_loc, $output_html, "dir"=>"", "type"=>"A", "scale"=>"none");
    }
}

###
### MAIN
###
if (scalar(@ARGV) != 1) {
    die "Bad arguments: $USAGE";
}
my ($a_info_file) = @ARGV;
my ($page_title, $pics, $simple_output, $simple_loc, $script_output, $script_loc) = get_album_info($a_info_file);
read_locs();
if ($upload_pics) {
    upload_pics($pics);
}
if (defined($simple_output)) {
    output_simple_thumbs($simple_output, $simple_loc, $use_local_page, $upload_page, $page_title, $pics);
    if (defined($script_output)) {
	chomp(my $simple_dir = `dirname $simple_output`);
	chomp(my $simple_base = `basename $simple_output`);
	output_script($script_output, 
		      $script_loc,
		      get_loc_url($simple_loc, $use_local_page, $simple_dir, "dir"=>"") 
		        . $simple_base,
		      $use_local_page, 
		      $upload_page, 
		      $page_title, 
		      $pics);
    }
}
close_ftp();
