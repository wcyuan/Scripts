#!/usr/local/bin/perl -w
#
# lesspipe.sh knows how to automatically decompress files.  So this
# wrapper knows that if you can't find a file, look for the compressed
# version.  lesspipe.sh only appears on Linux.
#
# The only problem with this is that the filename that appears in the
# bar at the bottom of the less window will still say the original
# filename (without the suffix), which is a bit misleading.
#
# Less shortcuts that are worth remembering:
#
#  123g     -> jump to line 123
#  12%      -> jump to 12% through the file
#
#  /*patt   -> search for the pattern across all files
#  /!patt   -> search for the opposite of pattern
#  /^Kpatt  -> hilite pattern w/o moving
#  /^Rpatt  -> search for patt as a string, not a regexp
#  esc-n    -> repeat previous search across all files
#  -a       -> 'n' repeats the search, but starting with the next screen
#  -p<patt> -> open the file starting with the first occurrence of <patt>
#

use strict;
my $LESSPIPE = '/usr/bin/lesspipe.sh';
my @SUFFIXES = qw(gz bz2);

my $file = $ARGV[0];
if (-x $LESSPIPE) {
    if (! -e $file) {
        foreach my $sfx (@SUFFIXES) {
            if (-e "$file.$sfx") {
                $file = "$file.$sfx";
                last;
            }
        }
    }
    exec("$LESSPIPE $file");
}
