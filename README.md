Fuzzy Log File Grouper
======================

A quick-and-dirty tool for grouping together similar log files based on a
simple fuzzy string matching process.

Motivation
----------

Imagine you're running an experiment many, many times, probably in parallel.
Each time the experiment runs a log file is produced.  Sometimes the experiment
goes awry and crashes with a lengthy error report being written into the log
file.

To try and fix the problem you might start by looking through each log file in
turn to try and find which ones contain errors. You quickly tire of this and
write a simple grep-based script to list all the logs which didn't end with
success.

Now you've got a whole pile of log files which you know contain error reports.
You start leafing through them to find that there seem to follow a just a few
patterns, for example, some might segfault at a particular point while others
throw some kind of internal error.

Unfortunately, re-running the experiment takes a while so you want to be sure
you've fixed all of the bugs you've seen in your logs before trying again. You
could try and write a greppy-one-liner to eliminate log files for the classes
of problems you've seen. Unfortunately this risks accidentally eliminating the
wrong log files if your regexes aren't specific enough. Plus all this takes a
whole lot of effort and you don't want to have to keep doing it.

Enter the fuzzy log file grouping tool... This tool compares your stack of
logfiles and groups together files with very similar contents. It uses fuzzy
string matching to avoid being tripped up unimportant details. It can also
optionally deploy simple heuristics to avoid being misled by, for example,
pointer addresses in the log.

Usage
-----

Just run the script passing it all of your logfile's filenames as arguments.

    $ python fuzzy_grouper.py <FILE1> ...

The tool lists the files, one per file, in groups seperated by an empty line.

The similarity threshold can be set using the `--threshold` option which
defaults to 0.9. To help choose a good threshold, start with something high
(e.g. 0.99) and use the `--print-similarity-matrix` option to print the
similarity scores matrix between the resulting groups. Find examples of groups
which you think should be merged and check their similarity score in the
matrix. Use this score to try a new, lower similarity score.

See `--help` for more options!
