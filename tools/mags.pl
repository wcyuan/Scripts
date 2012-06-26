#!/usr/bin/env perl
#

use strict;
use warnings 'all';
use WWW::Mechanize;
use Data::Dumper;
use Text::Table;
use HTML::TreeBuilder;
use Getopt::Long;
use Log::Log4perl qw(:levels);

# -----------------------------------------------------------

my $PAGE = 'http://desco.csubs.com';
my $USER = 'yuanc@deshaw.com';
my $PASS = 'rl4djun3';

Log::Log4perl->easy_init($ERROR);
my $LOGGER = Log::Log4perl->get_logger();

# -----------------------------------------------------------

sub main() {

    GetOptions( "dump=s"      => \my $dump_file,
                "parse=s"     => \my $parse_file,
                "page=i"      => \my $given_pageno,
                "verbose"     => sub { $LOGGER->level($DEBUG) },
                "log_level=s" => sub { $LOGGER->level($_[1]) },
              )
        or die("Error parsing options");

    if ($parse_file) {
        parse_page(file => $parse_file);
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

    my $pageno = 1;
    my $table = new Text::Table('page', 'price', 'name', 'desc');
  PAGE:
    while(1) {
        my $uri = $mech->uri();
        if ($uri =~ m/page=(\d+)$/) {
            $pageno = $1;
        }
        if (defined($given_pageno) && $given_pageno != $pageno) {
            my $new_uri = $uri;
            $new_uri =~ s/page=(\d+)$/page=$given_pageno/;
            $LOGGER->debug("getting $new_uri");
            $mech->get($new_uri);
            $pageno = $given_pageno;
        }
        parse_page($table, $pageno, content => $mech->content());

        if (defined($given_pageno)) {
            $table =~ s/\s*\n/\n/g;
            print $table;
            return;
        }

        my @links = $mech->
            find_all_links(text_regex => qr(^\d+$),
                           url_regex  => qr(^search_handler\.cfm\?page=\d+$),
                          );

        foreach my $link (@links) {
            #print "url : " . ($link->url()//"")  . "\n";
            #print "text: " . ($link->text()//"") . "\n";
            my $url = $link->url();
            if ($url =~ m/page=(\d+)$/) {
                my $linkno = $1;
                if ($linkno == $pageno+1) {
                    $mech->get($url);
                    $LOGGER->debug("getting $url");
                    next PAGE;
                }
            }
        }

        $table =~ s/\s*\n/\n/g;
        print $table;
        return;
    }
}

sub dfs($$) {
    my ($tree, $visit) = @_;
    my @nodes = ($tree);
    while (my $node = pop(@nodes)) {
        if (!$visit->($node)) {
            next;
        }
        unshift(@nodes, grep {ref($_)} reverse($node->content_list()));
    }
    return;
}

# returns a list
sub get_text($) {
    my ($tree) = @_;
    my @text;
    dfs($tree, sub {
            my ($node) = @_;
            my $class = $node->attr('class');
            push(@text, map {
                [ $_, $class ]
            } grep {
                !ref($_)
            } reverse($node->content_list()));
            return 1;
        });
    return @text;
}

sub parse_page($$%) {
    my ($table, $pageid, %opt) = @_;
    my $tree;
    if ($opt{file}) {
        $tree = HTML::TreeBuilder->new_from_file($opt{file});
    } else {
        $tree = HTML::TreeBuilder->new_from_content($opt{content});
    }

    dfs($tree, sub {
            my ($node) = @_;
            if ($node->tag() eq 'tr') {
                if (0) {
                    print "-----------------\n";
                    print("lineage: ",
                          join(',', reverse($node->lineage_tag_names())),
                          "\n");
                    foreach my $attr ($node->all_attr_names()) {
                        print("$attr -> ", $node->attr($attr), "\n");
                    }
                }

                my ($name, $ver, $desc, $price);
                my @texts = get_text($node);
                foreach my $entry (@texts) {
                    my ($text, $class) = @$entry;
                    $class //= '';
                    if ($class eq 'pub') {
                        $name = $text;
                    }
                    elsif ($class eq 'ver') {
                        $ver = $text;
                    }
                    elsif ($class eq 'description_short') {
                        $desc = $text;
                    }
                    elsif ($text =~ /^\s*\$/) {
                        $price = $text;
                    }
                }
                if (defined($name)) {
                    $desc //= '';
                    if (defined($ver)) {
                        $name .= " ($ver)";
                    }
                    $table->add($pageid, $price, $name, $desc);
                }
                return 0;
            } else {
                return 1;
            }
        });
}

# -----------------------------------------------------------

main();

