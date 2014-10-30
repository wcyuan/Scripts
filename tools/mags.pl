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

my $PAGE = 'https://desco.csubs.com';
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

    my $table = new Text::Table('page', 'price', 'nissues', 'name', 'category', 'desc');
    if ($parse_file) {
        parse_page($table, 0, file => $parse_file);
        $table =~ s/\s*\n/\n/g;
        print $table;
        return;
    }

    my $mech = WWW::Mechanize->new();

    # --- Login --------------------------- #

    $LOGGER->debug("getting $PAGE");
    $mech->get($PAGE);
    $LOGGER->debug("logging in");
    $mech->submit_form(form_name => 'form1',
                       fields => {
                                  login_username => $USER,
                                  login_password => $PASS,
                                 });
    if (!$mech->success()) {
        die("Couldn't login.");
    }
    $LOGGER->debug("logged in");

    # --- View Publication List ----------- #

    # The site has changed, nothing after this works anymore...
    $mech->submit_form();

    # --- Start printing the magazines ---- #

    my $pageno = 1;
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

        if ($dump_file) {
            open(FD, ">$dump_file")
                or die("Can't write to $dump_file: $? $! $@");
            print FD $mech->content();
            close(FD)
                or warn("Can't close $dump_file: $? $! $@");
            return;
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
            my %attrs = $node->all_attr();
            push(@text, map {
                [ $_, $class, \%attrs ]
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
    # Each element of the tree is an HTML::Element.  Perldoc that for
    # more information.
    #
    # My understanding: an element represents an HTML tag --
    # i.e. every tag on a page is an element.  The content of that
    # element is a list, where each thing in the list is either an
    # element or text.

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

                my ($name, $ver, $desc, $price, $category, $nissues);
                my @texts = get_text($node);
                foreach my $entry (@texts) {
                    my ($text, $class, $attrs) = @$entry;
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
                    elsif (defined($attrs->{href}) &&
                           # this just happens to be the links they use for categories
                           $attrs->{href} =~ /search_handler.cfm\?category/)
                    {
                        $category = $text;
                    }
                    elsif ($text =~ /^\s*\$/) {
                        $price = $text;
                    }
                    elsif (defined($attrs->{style}) &&
                           # this just happens to be the style they use for number of issues
                           $attrs->{style} =~ /padding-right: 8px; text-align: right;/)
                    {
                        $nissues = $text;
                    }
                }
                if (defined($name)) {
                    $desc //= '';
                    if (defined($ver)) {
                        $name .= " ($ver)";
                    }
                    $table->add($pageid, $price, $nissues, $name, $category, $desc);
                }
                return 0;
            } else {
                return 1;
            }
        });
}

# -----------------------------------------------------------

main();

