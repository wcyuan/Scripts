#!/usr/local/bin/perl -w
#
# $Id: sched_stats.pl,v 1.85 2011/12/29 16:16:34 yuanc Exp $
# $Source: /u/yuanc/testbed/perl/random/RCS/sched_stats.pl,v $
#
# sched_stats.pl
# @desc:  Print some information about the tennis schedule.
#
# Conan Yuan, 20070924
#

=head1 NAME

sched_stats.pl - Print some information about the tennis schedule.

=head1 SYNOPSIS

  sched_stats.pl [options] 

  Options: 
    --help, -?        shows brief help message
    --perldoc         shows full documentation

  See also Getopt::Long for complete standard options list.

=head1 ARGUMENTS

=over

None.

=back

=head1 OPTIONS

=over 4

=item I<--help>

Print a brief help message and exit.

=item I<--perldoc>

Print the perldoc page and exit.

=back

=head1 DESCRIPTION

Print some information about the tennis schedule

=cut

use strict;
use warnings 'all';
use Pod::Usage;

use Getopt::Long;
use Text::Table;

# ----------------------
# Hard-coded per-season values

# ----------------------
# data for 2007
my $cost_per_season2007 = 5120;
# holidays == days when we don't expect to have 4 people.  
my %holidays2007 = (8 => 1, # thanksgiving,
		    20 => 1, # not really a holiday, but no one can make it
		   );

my %paid2007 = ("lawryj" => 360 + 400,
		"aizenman" => 320 + 320,
		"boguslaa" => 320 + 320,
		"elassalk" => 320 + 200,
		"starka" => 680,
		"reiss" => 720, # actually he paid $680, since I subbed for him once, so it's as if he paid $720 and I paid him $40 for the sub
	       );

my %is_regular2007 = ("aizenman" => 1, 
		      "boguslaa" => 1, 
		      "elassalk" => 1,
		      "lawryj"   => 1,
		      "reiss"    => 1,
		      "starka"   => 1,
		      "yuanc"    => 1);


# XXX not sure what happened on the 20th -- could have been andy and peter playing singles
my $actual2007 = 
'week date      aizenman boguslaa elassalk lawryj reiss starka yuanc sub none none2
1  20071004	       1	0	 1	0     X	     1     1   0    0     0
2  20071011	       0	1	 0	1     1	     0     1   0    0     0  (peter hurt)
3  20071018	       1	0	 X	1     X	     1	   1   0    0     0  dress rehearsal
4  20071025	       1	0	 0	1     X	     $	   1   0    0     0
5  20071101	       1	1	 X	1     X	     0	   1   0    0     0  was originally andys, gave it to james
6  20071108	       0	1	 1	0     $	     P	   1   0    0     0
7  20071115	       1	0	 $	1     X	     X	   1   P    0     0  (yair late due to prop poker tournament)
8  20071122	       -	-	 -	-     -	     -	   -   0    0     0  thanksgiving
9  20071129	       1	1	 $	0     1	     0	   X   P    0     0  dress rehearsal
10 20071206	       0	1	 1	X     $	     1	   P   0    0     0  chanukah/ops. was originally james, gave it to andy
11 20071213	       P	1	 0	$     0	     $	   1   0    P     0
12 20071220	       $	0	 0	$     1	     1 	   X   0    P     P  right before xmas - in SFO
13 20071227	       P	X	 1	X     1	     $	   1   0    0     0  right before new years
14 20080103	       P	0	 0	1     1	     $	   1   0    0     0
15 20080110	       1	$	 $	0     P	     0	   1   P    0     0
16 20080117	       0	1	 1	$     X	     $	   0   0    P     P  right before mlk day
';

# unused
my $separate_by_ability2007 = 
'week date      aizenman boguslaa elassalk lawryj reiss starka yuanc sub
1  20071004	       0	0	 0	1     1	     1     1   0
2  20071011	       1	1	 1	0     0	     0     1   0
3  20071018	       1	0	 X	1     1	     1	   X   0  dress rehearsal
4  20071025	       0	0	 0	1     1	     1	   1   0
5  20071101	       1	1	 X	0     0	     1	   1   0
6  20071108	       0	1	 1	0     1	     0	   1   0
7  20071115	       1	0	 1	1     0	     X	   1   0
8  20071122	       -	-	 -	-     -	     -	   -   0  thanksgiving
9  20071129	       1	1	 1	0     1	     ?	   X   0  dress rehearsal
10 20071206	       0	1	 1	1     1	     0	   ?   0  chanukah/ops
11 20071213	       0	0	 0	1     1	     1	   1   0
12 20071220	       1	1	 0	1     0	     1 	   X   0  to SFO
13 20071227	       X	X	 1	X     X	     1	   1   1  right before new years
14 20080103	       0	0	 0	1     1	     1	   1   0
15 20080110	       1	1	 1	0     0	     0	   1   0
16 20080117	       0	1	 1	1     X	     1	   0   0  right before mlk day
';

# unused
my $evenly_spaced2007 = 
'week date      aizenman boguslaa elassalk lawryj reiss starka yuanc sub
1  20071004	       0	0	 0	1     1	     1     1   0
2  20071011	       1	1	 1	0     0	     0     1   0
3  20071018	       1	0	 X	1     1	     1	   X   0  dress rehearsal
4  20071025	       0	1	 1	0     1	     1	   0   0
5  20071101	       1	-	 X	1     0	     1	   1   0
6  20071108	       0	1	 1	0     1	     0	   1   0
7  20071115	       1	0	 1	1     0	     X	   1   0
8  20071122	       -	-	 -	-     -	     -	   -   0  thanksgiving
9  20071129	       0	1	 1	1     1	     ?	   X   0  dress rehearsal
10 20071206	       0	1	 1	1     0	     1	   ?   0  chanukah/ops
11 20071213	       1	0	 0	0     1	     1	   1   0
12 20071220	       0	1	 0	1     1	     0 	   1   0  right before xmas
13 20071227	       X	X	 1	X     X	     1	   1   1  right before new years
14 20080103	       1	0	 0	1     1	     1	   0   0
15 20080110	       1	1	 1	0     0	     0	   1   0
16 20080117	       0	1	 0	1     X	     1	   1   0  right before mlk day
';

my $second_half_conflicts2007 = 
'week date      aizenman boguslaa elassalk lawryj reiss starka yuanc sub
17 20080124	       .	.	 .	.     X	     .	   .   .
18 20080131	       X	.	 X	.     .	     X	   .   .
19 20080207	       X	.	 X	.     .	     .	   .   .
20 20080214	       X	.	 X	.     X	     X	   ?   .  Harvard interviews
21 20080221	       X	.	 .	.     .	     .	   .   .
22 20080228	       .	.	 .	.     X	     .	   .   .
23 20080306	       .	.	 .	.     .	     .	   ?   .  to SFO?
24 20080313	       .	.	 .	.     .	     .	   ?   .  to SFO?
25 20080320	       .	.	 .	.     .	     .	   ?   .  to SFO? (night before purim)
26 20080327	       .	.	 .	.     .	     .	   .   .  ops
27 20080403	       .	.	 .	.     .	     .	   .   .
28 20080410	       .	.	 .	.     X	     .	   .   .  HGC alum weekend
29 20080417	       .	.	 .	.     .	     .	   .   .
30 20080424	       .	X	 X	.     .	     .	   X   .  passover
31 20080501	       .	.	 .	.     .	     .	   .   .
32 20080508	       .	.	 .	.     .	     .	   .   .
';

my $second_half2007 = 
'week date      aizenman boguslaa elassalk lawryj reiss starka yuanc sub sub2 sub3 none1 none2 none3
17 20080124	       1	0	 X	0     1	     1	   $   P    0    0     0     0     0  to SFO
18 20080131	       X	$	 X	$     1	     X	   1   0    0    0     0     0     0
19 20080207	       X	X	 X	1     1	     1	   1   0    0    0     0     0     0
20 20080214	       X	X	 X	$     P	     X	   1   0    0    0     1     1     0  Harvard interviews
21 20080221	       X	0	 0	1     1	     1	   1   0    0    0     0     0     0
22 20080228	       1	1	 0	$     X	     $	   P   0    0    0     0     0     0 
23 20080306	       1	1	 1	0     1	     X	   0   0    0    0     0     0     0 
24 20080313	       0	1	 $	0     1	     X	   1   P    0    0     0     0     0 
25 20080320	       1	1	 1	1     0	     0	   0   0    0    0     0     0     0  night before purim, ops
26 20080327	       1	0	 1	0     1	     0	   $   P    0    0     0     0     0  Dinner w/ Karen and Jim
27 20080403	       P	0	 0	1     1	     $	   1   0    0    0     0     0     0  
28 20080410	       1	$	 1	0     X	     P	   1   0    0    0     0     0     0  HGC alum weekend
29 20080417	       0	1	 0	1     0	     1	   $   P    0    0     0     0     0  to Ithaca for Pesach
30 20080424	       $	X	 X	1     1	     1	   X   0    0    0     0     0     0  passover
31 20080501	       1	$	 X	0     1	     0	   1   0    0    0     0     0     0 
32 20080508	       0	0	 0	1     1	     1	   1   0    0    0     0     0     0  
';


# ----------------------
# data for 2008
my $cost_per_season = 5344;
# holidays == days when we don't expect to have 4 people.  
my %holidays = (8 => 1, # thanksgiving,
		12 => 1, # christmas,
		#13 => 1, # new year's,
	       );

my %is_regular = ("boguslaa" => 1, 
		  "fulenwiw" => 1,
		  "lawryj"   => 1,
		  "reiss"    => 1,
		  "starka"   => 1,
		  "yuanc"    => 1);

my %paid = ("fulenwiw" => 431.32 + 417.50, 
	    "lawryj"   => 431.42 + 417.50, 
	    "boguslaa" => 389.67 + 417.50,
	    "starka" => 848.92,
	    "sub1" => 42);

my $just_conflicts2008 = 
'week date        boguslaa chenjo fulenwiw lawryj reiss starka yuanc sub
1  20081009              X      0        0      X     1      X     X   0  Yom Kippur
2  20081016              0      0        0      0     0      X     0   0  Sukkot (not yuntiff)
3  20081023              X      0        0      0     0      0     0   0  
4  20081030              0      0        0      0     0      0     0   0  
5  20081106              0      0        0      0     0      0     0   0  
6  20081113              0      0        0      0     0      0     0   0  
7  20081120              0      0        0      0     0      X     0   0  
8  20081127              X      X        X      X     X      X     X   0  Thanksgiving
9  20081204              0      0        0      0     0      0     X   0  Honeymoon?
10 20081211              0      X        0      0     0      0     X   0  Honeymoon?
11 20081218              0      0        0      0     0      0     X   0  Honeymoon?
12 20081225              0      X        X      X     X      X     ?   0  Christmas/Chanukah
13 20080101              X      0        0      1     1      X     ?   0  New Years Day
14 20090108              0      0        0      0     0      0     0   0  
15 20090115              0      0        0      0     X      0     0   0  Before MLK day weekend
16 20090122              0      0        0      0     X      X     0   0  
';


my $actual2008 = 
'week date        boguslaa fulenwiw lawryj reiss starka yuanc   sub1 sub
1  20081009              X        1      X     1      X     1      1   0  Yom Kippur
2  20081016              1        1      1     0      X     1      0   0  Sukkot (not yuntiff)
3  20081023              X        0      1     1      1     1      0   0  
4  20081030              $        1      0     0      1     1      P   0  Murali subs for Alisa
5  20081106              0        0      1     1      1     1      0   0  
6  20081113              1        1      0     0      1     1      0   0  
7  20081120              1        0      1     $      X     1      P   0  Jo Chen subs for Peter because of annual Poker outing
8  20081127              X        X      X     X      X     X      X   0  Thanksgiving
9  20081204              1        1      0     1      1     X      0   0  Honeymoon
10 20081211              0        1      1     1      1     X      X   0  Honeymoon
11 20081218              1        0      1     1      1     X      0   0  Honeymoon
12 20081225              0        X      X     X      X     ?      X   0  Christmas/Chanukah
13 20080101              X        $      1     1      X     1      0   0  New Years Day
14 20090108              1        0      0     1      1     1      0   0  
15 20090115              0        1      1     P      $     1      0   0  Before MLK day weekend
16 20090122              $        1      $     X      X     1      P   P  Tom de Swardt subs for James, Melanie Eisen subs for Alisa
';

my $second_half_conflicts2008 = 
'week date        boguslaa fulenwiw lawryj reiss starka yuanc   sub1 sub
17 20090129              0        0      X     0      X     0      X   0  
18 20090205              0        X      0     0      X     0      0   0  Ellie in India
19 20090212              X        0      X     0      0     0      0   0  Before Presidents day weekend; Ellie in India
20 20090219              X        0      0     0      0     0      0   0  
21 20090226              0        0      0     0      0     0      0   0  
22 20090305              0        0      ?     X      0     0      0   0  
23 20090312              0        0      ?     0      0     0      0   0  After "poker tells" talk
24 20090319              0        0      0     0      X     0      0   0  
25 20090326              0        0      0     0      0     0      0   0  
26 20090402              0        0      0     0      0     0      0   0  
27 20090409              X        0      0     X      X     X      X   0  Second night of Passover
28 20090416              0        0      0     0      0     ?      0   0  Right after the end of Passover
29 20090423              0        0      0     0      0     0      0   0  
30 20090430              0        0      0     0      0     0      0   0  
31 20090507              0        0      0     0      0     0      0   0  
32 20090514              0        0      0     0      0     0      0   0  
';

my $second_half2008 = 
'week date        boguslaa fulenwiw lawryj reiss starka yuanc   sub1 sub
17 20090129              1        1      X     1      X     1      X   0  
18 20090205              $        X      1     1      P     1      0   0  Ellie in India
19 20090212              X        1      X     $      $     $      P   P  Before Presidents day weekend; Both in India; je-luen li subbed for peter
20 20090219              X        0      1     1      1     1      0   0  
21 20090226              $        1      1     0      0     1      0   0  
22 20090305              $        $      ?     X      1     1      P   0  Je Li played for Wendy
23 20090312              $        1      ?     1      P     1      0   0  After "poker tells" talk
24 20090319              $        0      1     $      P     1      0   0  Peter looking for a sub
25 20090326              $        1      1     0      1     0      0   0  * To SF
26 20090402              0        0      1     1      $     1      0   0  * 
27 20090409              X        1      1     X      X     X      1   1  * (jochen is busy) Second night of Passover
28 20090416              $        1      1     0      1     ?      0   0  * Right after the end of Passover
29 20090423              0        0      1     1      1     1      0   0  
30 20090430              $        1      0     0      1     1      0   0  * 
31 20090507              0        0      1     1      1     1      0   0  
32 20090514              $        1      0     1      1     0      0   0  *I can probably play
';

# ----------------------
# Constants across all seasons
my $players_per_week = 4;
my $weeks_per_season = 32;


# Parse any command-line options
GetOptions("first!" => \my $first,
	   "second!" => \my $second,
	   "2007!" => \my $use_2007_data,
	  )
    or pod2usage();

# Parse any script arguments
pod2usage("Wrong number of arguments") unless @ARGV == 0;


my $schedule;
if (!$first && !$second) {
    # default to just the first half of the season...
    $first = 1;
    $second = 1;
}
if ($use_2007_data) {
    if ($first) {
	$schedule .= $actual2007;
    }
    if ($second) {
	if ($first) {
	    # remove the header
	    my @lines = split("\n", $second_half2007);
	    shift(@lines);
	    $schedule .= join("\n", @lines);
	} else {
	    $schedule .= $second_half2007
	}
    }
    %paid = %paid2007;
    %holidays = %holidays2007;
    $cost_per_season = $cost_per_season2007;
    %is_regular = %is_regular2007;
} else {
    if ($first) {
	$schedule .= $actual2008;
    }
    if ($second) {
	if ($first) {
	    # remove the header
	    my @lines = split("\n", $second_half2008);
	    shift(@lines);
	    $schedule .= join("\n", @lines);
	} else {
	    $schedule .= $second_half2008;
	}
    }
}

# ----------------------
# munge data

sub is_playing ( $ ) {
    my ($var) = @_;
    return ($var eq 1 || $var eq "P");
}

sub is_paying ( $ ) {
    my ($var) = @_;
    return ($var eq 1 || $var eq '$' || $var eq "C");
}

# this means that the player is not playing, but is available to play
# if necessary (according to the data).
sub can_play ( $ ) {
    my ($var) = @_;
    return ($var eq 0);
}

# this means that a player is scheduled to play, but has a conflict
# and is looking to swap.
sub has_conflict ( $ ) {
    my ($var) = @_;
    return ($var eq 'C');
}

sub read_data ( $ ) {
    my ($data) = @_;
    # read data
    my @lines = split('\n', $data);
    my @players = split(' ', shift(@lines));
    my @weeks;
    foreach my $line (@lines) {
	my @one_week_list = split(' ', $line);
	my %one_week;
	foreach my $player (@players) {
	    $one_week{$player} = shift(@one_week_list);
	}
	push(@weeks, \%one_week);
    }
    shift(@players);
    shift(@players);

    # Count
    my %by_player;
    my %by_paying_player;
    my %paired;
    foreach my $week (@weeks) {
	my $nplayers = 0;
	my $npayers  = 0;
	foreach my $player (@players) {
	    foreach my $other_player (@players) {
		if (!defined($paired{$player}{$other_player})) {
		    $paired{$player}{$other_player} = 0;
		}
	    }
	    if (!defined($by_player{$player}{nweeks})) {
		$by_player{$player}{nweeks} = 0;
	    }
	    if (!defined($by_paying_player{$player}{nweeks})) {
		$by_paying_player{$player}{nweeks} = 0;
	    }
	    if (is_playing($week->{$player})) {
		$nplayers++;
		$by_player{$player}{nweeks}++;
		push(@{$by_player{$player}{dates}}, $week->{date});
		push(@{$by_player{$player}{weeks}}, $week->{week});
		foreach my $other_player (@players) {
		    if ($player eq $other_player) {
			$paired{$player}{$other_player} = "-";
		    } else {
			if (is_playing($week->{$other_player})) {
			    $paired{$player}{$other_player}++;
			}
		    }
		}
	    }
	    if (is_paying($week->{$player})) {
		$npayers++;
		$by_paying_player{$player}{nweeks}++;
		push(@{$by_paying_player{$player}{dates}}, $week->{date});
		push(@{$by_paying_player{$player}{weeks}}, $week->{week});
	    }
	}
	if (!$holidays{$week->{week}} &&
	    ($nplayers > $players_per_week || $npayers != $players_per_week)) {
	    die("Bad week $week->{week}, $nplayers players, $npayers payers: " . $lines[$week->{week}-1]);
	}
    }

    return (\@players, \@weeks, \%by_player, \%paired, \%by_paying_player);
}

my ($players, $weeks, $by_player, $paired, $by_paying_player) = read_data($schedule);

# ----------------------
# find swaps

# A is playing on week X and wants to swap out.  find a player B who
# is not playing on week X who can play on week X.  in order to swap,
# there must also exist a week Y who is there also must exist week Y
# where B is playing and A is not playing, but where A is available to
# play.
sub find_swap ( $$$ ) {
    my ($player, $week, $weeks) = @_;

    my @other_players;
    foreach my $other_player (keys %$week) {
	if ($player eq $other_player) {
	    next;
	}
	if (!is_playing($week->{$other_player}) &&
	    can_play($week->{$other_player})) {
	    push(@other_players, $other_player);
	}
    }

    my @possibilities;
    foreach my $other_week (@$weeks) {
	if ($week->{week} == $other_week->{week}) {
	    next;
	}
	foreach my $other_player (@other_players) {
	    if (is_playing($other_week->{$other_player}) &&
		!is_playing($other_week->{$player}) &&
		can_play($other_week->{$player})) {
		push(@possibilities, [$other_player, $other_week]);
	    }
	}
    }
    return \@possibilities;
}

sub find_all_swaps ( $ ) {
    my ($weeks) = @_;
    foreach my $week (@$weeks) {
	foreach my $player (keys %$week) {
	    if (has_conflict($week->{$player})) {
		print "looking for swaps for $player on week $week->{week}\n";
		my $posses = find_swap($player, $week, $weeks);
		foreach my $poss (@$posses) {
		    my ($other_player, $other_week) = @$poss;
		    print "swap with $other_player on $other_week->{week} $other_week->{date}\n";
		}
	    }
	}
    }
}

# ----------------------
# Output


# -----------------------------------------------------
# swaps
find_all_swaps ($weeks);

# -----------------------------------------------------
# the schedule
my $tb = new Text::Table("", "", map { {title=>$_, align=>'left'} } @$players);
foreach my $week (@$weeks) {
    $tb->add(map {$week->{$_}} ("week", "date", @$players));
}

# -----------------------------------------------------
# cost
my $cost_per_week = $cost_per_season / $weeks_per_season;
my $cost_per_person_per_week = $cost_per_week / $players_per_week;
my $cost_of_holidays = scalar(keys(%holidays)) * $cost_per_week;
my $cost_of_holidays_per_person = $cost_of_holidays / scalar(keys(%is_regular));

{
    my %n_played;
    my %n_pays;
    my %cost;
    my %cost_w_hol;
    my %owes;
    foreach my $player (@$players) {
	$n_played{$player} = $by_player->{$player}{nweeks};
	$n_pays{$player}   = $by_paying_player->{$player}{nweeks};
	$cost{$player}     = $n_pays{$player} * $cost_per_person_per_week;
	if ($is_regular{$player}) {
	    $cost_w_hol{$player} = sprintf "%0.2f", $cost{$player} + $cost_of_holidays_per_person;
	} else {
	    $cost_w_hol{$player} = sprintf "%0.2f", $cost{$player};
	}
	$owes{$player} = sprintf "%0.2f", ($cost_w_hol{$player} - ($paid{$player} || 0));
    }
    $tb->add("", "#played",       map {$n_played{$_}}    @$players);
    $tb->add("", "#paid",         map {$n_pays{$_}}      @$players);
    $tb->add("", "\$cost",        map {$cost{$_}}        @$players);
    $tb->add("", "\$cost w/ hol", map {$cost_w_hol{$_}}  @$players);
    $tb->add("", "\$paid",        map {($paid{$_} || 0)} @$players);
    $tb->add("", "\$owes",        map {$owes{$_}}        @$players);
    print $tb;
}

# cost of holidays:
print "cost of holidays: $cost_of_holidays\n";
print "cost of holidays per person: $cost_of_holidays_per_person\n";

print "\n";

# -----------------------------------------------------
# how many times each player plays with each other regular player
$tb = new Text::Table("", @$players);
foreach my $player (@$players) {
    $tb->add($player, map {$paired->{$player}{$_}} @$players);
}
{
    my %ave_others;
    foreach my $player (@$players) {
	my $n_others = 0;
	my $n_other_weeks = 0;
	foreach my $other_player (@$players) {
	    if ($is_regular{$other_player} && $other_player ne $player) {
		$n_other_weeks += $paired->{$player}{$other_player};
		$n_others++;
	    }
	}
	$ave_others{$player} = sprintf("%.2f", $n_other_weeks / $n_others);
    }
    $tb->add("ave", map { $ave_others{$_} } @$players);
}
print $tb;

print "\n";

# -----------------------------------------------------
# the schedule with words
$tb = new Text::Table();
foreach my $week (@$weeks) {
    if (0) {
	$tb->add($week->{week},
                 $week->{date},
                 grep {is_playing($week->{$_})} @$players);
    } else {
	$tb->add($week->{week},
                 $week->{date},
                 map {is_playing($week->{$_}) ? $_ : ($is_regular{$_} ? "-" : "")} @$players);
    }
}
print $tb;

if (0) {
    print "\n";
    $tb = new Text::Table();
    # the schedule per player
    foreach my $player (@$players) {
	$tb->add($player, @{$by_player->{$player}{dates}});
    }
    print $tb;
}

# ----------------------

__END__

=head1 AUTHOR

 Conan Yuan
 $Revision: 1.85 $
 $Source: /u/yuanc/testbed/perl/random/RCS/sched_stats.pl,v $

=cut

