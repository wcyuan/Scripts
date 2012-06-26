#!/usr/local/bin/perl -w
#
# $Header: /u/yuanc/testbed/perl/RCS/mags.pl,v 1.2 2012/06/25 21:22:32 yuanc Exp $
#

use WWW::Mechanize;
use Data::Dumper;
use HTML::Parser;
use HTML::TreeBuilder;
use Getopt::Long;

# -----------------------------------------------------------

my $PAGE = 'http://desco.csubs.com';
my $USER = 'yuanc@deshaw.com';
my $PASS = 'rl4djun3';


# -----------------------------------------------------------

sub main() {

    GetOptions( "dump=s"  => \my $dump_file,
                "parse=s" => \my $parse_file,
              )
        or die("Error parsing options");

    if ($parse_file) {
        parse_page($parse_file);
        return;
    }

    my $mech = WWW::Mechanize->new();

    # --- Login --------------------------- #

    $mech->get($PAGE);
    $mech->submit_form(form_name => 'form1',
                       fields => {
                                  login_username => $USER,
                                  login_password => $PASS,
                                 });
    if (!$mech->success()) {
        die("Couldn't login.");
    }

    # --- View Publication List ----------- #

    $mech->submit_form();

    if ($dump_file) {
        open(FD, ">$dump_file")
            or die("Can't write to $dump_file: $? $! $@");
        print FD $mech->content();
        close(FD)
            or warn("Can't close $dump_file: $? $! $@");
        return;
    }

    # --- Start printing the magazines ---- #

    while(1) {
        parse_page($mech->content());

        my @links = $mech->
            find_alls_link(text_regex => /^\d+$/,
                           url_regex  => /^search_handler\.cfm\?page=\d+$/,
                          );

        foreach my $link (@links) {
            print "url : " . ($link->url()//"")  . "\n";
            print "text: " . ($link->text()//"") . "\n";
            #print "name: " . $link->name() . "\n";
            #print "tag : " . $link->tag()  . "\n";
            #print "base: " . $link->base() . "\n";
        }

        return;
    }
}

sub parse_page($) {
    my ($page) = @_;
    my $tree = HTML::TreeBuilder->new_from_file($page);

    my @nodes = ($tree);
    foreach my $node (@nodes) {
        if (!ref($node)) {
            print "nopath!\n";
            print "$node\n";
            next;
        }
        my @path = $node->lineage_tag_names();
        foreach my $child ($node->content_list()) {
            if (ref($child)) {
                push(@nodes, $child);
            } else {
                print "path: " . join(':', (@path, $node->tag())) . "\n";
                $child =~ s/\n//g;
                print "text: $child\n";
            }
        }
    }
}

# -----------------------------------------------------------

main();

