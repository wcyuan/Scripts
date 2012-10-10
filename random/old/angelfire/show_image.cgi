#!/usr/bin/perl -w
#
use strict;
use CGI::Pretty qw(:standard -debug);
my $q = new CGI::Pretty;

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

sub get_pic ( $$$ ) {
    my ($type,$album,$pic) = @_;
    my $web_dir = "/" . $album;
    return join("/", ($web_dir,$type,$pic));
}

sub get_url ( $$% ) {
    my ($q, $old_params, %new_params) = @_;
    foreach my $key (keys %new_params) {
	$old_params->{$key} = $new_params{$key};
    }
    return $q->url() . "?" . join("&", map { $_ . "=" . $old_params->{$_} } keys(%$old_params));
}

sub get_list ( $ ) {
    my ($album) = @_;
    if ( ! -r "/" . $album) {
	return ();
    }
    my @pics;
    my %reverse;
    my $ii = 0;
    open(LIST, "/" . $album)
      or die "Can't open /$album";
    while(<LIST>) {
	chomp;
	my $pic = $_;
	push(@pics,$pic);
	$reverse{$pic} = $ii;
	$ii++;
    }
    close(LIST);
    return (\@pics,\%reverse);
}

sub get_scale ( $$$ ) {
    my ($type, $album, $pic) = @_;
    my $dim = "width";
    my $scale = "80%";
    if ($type eq "thumb") {
	$scale = "100";
    }
    return ($dim, $scale);
}

my %params;
foreach my $param ($q->param()) {
    $params{$param} = $q->param($param);
}

print $q->header();
my %info = (style=>{type=>"text/css",
		    code=>page_style(),
		   });
if (defined($params{title})) {
    $info{title} = $params{title};
}
print $q->start_html(\%info);
if (!defined($params{album})) {
    print "<center>\n";
    print $q->p("No album to show.");
    print "</center\n>";
} else {
    if (defined($params{pic}) || 
	(defined($params{mode}) && ($params{mode} == "slideshow" ||
				    $params{mode} == "single"))) {
	my $pic;
	if (defined($params{pic})) {
	    $pic = $params{pic};
	} else {
	    my ($pics, $reverse) = get_list($params{album});
	    if (defined($pics->[0])) {
		$pic = $pics->[0];
	    }
	}
	print "<center>\n";
	if (!defined($pic)) {
	    print $q->p("No pic to show.");
	} else {
	    my ($dim, $scale) = get_scale("reg", $params{album}, $pic);
	    my %link = (href=>get_pic("full",$params{album},$pic));
	    if (defined($params{target})) {
		$link{target} = $params{target};
	    }
	    print $q->p($q->a(\%link, $q->img({src=>get_pic("reg",$params{album},$pic),
					       $dim=>$scale})));
	    my ($pics, $reverse) = get_list($params{album});
	    if (defined($reverse->{$pic})) {
		my $found = $reverse->{$pic};
		my @links;
		my %idxs = (
			    "first" => 0,
			    "prev" => $found - 1,
			    "next" => $found + 1,
			    "last" => $#{$pics},
			   );
		foreach my $link ("first", "prev", "next", "last") {
		    my $idx = $idxs{$link};
		    if (defined($pics->[$idx]) && $idx >= 0) {
			push(@links, $q->a({href=>get_url($q,\%params,"pic"=>$pics->[$idx])},$link));
		    }
		}
		if (scalar(@links) > 0) {
		    print $q->p(@links);
		}
	    }
	}
	print "</center\n>";
    } else {
	my ($pics, $reverse) = get_list($params{album});
	my @pic_html = ();
	foreach my $pic (@$pics) {
	    my ($dim, $scale) = get_scale("thumb", $params{album}, $pic);
	    my %link = (href=>get_url($q,\%params,"pic"=>$pic));
	    if (defined($params{target})) {
		$link{target} = $params{target};
	    }
	    push @pic_html, $q->a(\%link, $q->img({src=>get_pic("thumb",$params{album},$pic),
						   $dim=>$scale}));
	}
	print $q->p(@pic_html);
    }
}
print $q->end_html();
