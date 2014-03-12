#!/usr/local/bin/perl -w
#
# @desc: replace one set of strings with another set
#

=head1 SYNOPSIS

  replace.pl <old> <new> [files]*
  replace.pl -file <string_file> [-delim <delim>] [files]*

  each row of <string_file> should be
    <old string><delim><new string>

  <delim> defaults to "\s+"

=cut

# ---------------------------------------------------------------------------- #

use strict;
use warnings 'all';
use Pod::Usage;
use File::Temp;
use Getopt::Long;
use Log::Log4perl qw(:levels);

Log::Log4perl->easy_init($WARN);
my $LOGGER = Log::Log4perl->get_logger();

# ---------------------------------------------------------------------------- #

sub main() {
    my %strings;
    my @strings_list;
    my ($string_file, $by_word, $output_to_stdout, $FLAG_no_write) =
        parse_command_line();
    if ($string_file) {
        my $fd;
        open($fd, $string_file)
            or $LOGGER->logconfess("Can't open file $string_file: $? $! $@");
        while (my $line = <$fd>) {
            my ($old_string, $new_string) = split " ", $line;
            push(@strings_list, $old_string);
            $strings{$old_string} = $new_string;
            $LOGGER->debug("Adding $old_string -> $new_string");
        }
        close($fd)
            or $LOGGER->error("Error closing file $string_file: $? $! $@");
    } else {
        if (scalar(@ARGV) < 2) {
            pod2usage("Not enough arguments");
        }
        my $orig_str = shift(@ARGV);
        my $new_str = shift(@ARGV);
        $strings{$orig_str} = $new_str;
        push(@strings_list, $orig_str);
    }

    if (!%strings) {
        exit;
    }

    if (@ARGV) {
        foreach my $file (@ARGV) {
            do_file($file, \%strings, $by_word, $output_to_stdout,
                    $FLAG_no_write) ;
        }
    } else {
        while (my $line = <>) {
            print do_line($line, \%strings);
        }
    }
}

sub parse_command_line() {
    GetOptions("word|w!" => \my $by_word,
               "string_file|file|f=s" => \my $string_file,
               "output_to_stdout|stdout|o!" => \my $output_to_stdout,
               "no_write!" => \my $FLAG_no_write,
               "verbose" => sub { $LOGGER->level($DEBUG) },
               )
        or pod2usage();
    return ($string_file, $by_word, $output_to_stdout, $FLAG_no_write);
}

# ---------------------------------------------------------------------------- #

sub do_line ( $$;$ ) {
    my ($line, $strings, $by_word) = @_;
    foreach my $orig_str (keys %$strings) {
        my $re = $orig_str;
        my $new_string = $strings->{$orig_str};
        if ($by_word) {
            $re = '\b' . $re . '\b';
        }
        my $old_line = $line;
        $line =~ s/$re/$new_string/g;
        if ($old_line ne $line) {
            chomp($old_line);
            chomp(my $new_line = $line);
            $LOGGER->debug(
                "$orig_str -> $new_string | $old_line became $new_line");
        }
    }
    return $line;
}

sub do_file ( $$;$$$ ) {
    my ($file, $strings, $by_word, $output_to_stdout, $FLAG_no_write) = @_;
    my $in;
    open($in, $file);
    if (!$in) {
        $LOGGER->error("Can't open $file: $? $!");
        return;
    }
    my $tmpfile;
    if ($output_to_stdout) {
        $tmpfile = *STDOUT;
    } else {
        $tmpfile = new File::Temp();
    }
    my $file_changed = 0;
    while (my $line = <$in>) {
        my $newline = do_line($line, $strings, $by_word);
        if ($line ne $newline) {
            $file_changed = 1;
        }
        print $tmpfile $newline;
    }
    close($in)
        or $LOGGER->error("Can't close $in");
    if ($file_changed && !$output_to_stdout && !$FLAG_no_write) {
        system("cp " . $tmpfile->filename() . " $file") == 0
            or $LOGGER->logconfess("Couldn't copy $tmpfile to $file");
    }
    if ($file_changed) {
        $LOGGER->info("$file updated");
    } else {
        $LOGGER->info("no changes to $file");
    }
}

# ---------------------------------------------------------------------------- #

main();

# ---------------------------------------------------------------------------- #
