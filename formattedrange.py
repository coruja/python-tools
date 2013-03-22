#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
A class to convert a string containing a formatted range into a
list of strings in which the range has been expanded.

* Usage:
  % ./formattedrange.py "b[01-05]"
  b01 b02 b03 b04 b05

  % ./formattedrange.py "b[01,03-05]"
  b01 b03 b04 b05

  % ./formattedrange.py "b[01-02,05-10]"
  b01 b02 b05 b06 b07 b08 b09 b10

  NOTE: same command but without double quotes:
  % ./formattedrange.py b\[01-05\]

  %./formattedrange.py -f"%y%m%d" "b[201202026-20120301]c"
  b120226c b120227c b120228c b120229c b120301c

* The default delimiter is one space but it can be changed:
  % ./formattedrange.py -d $'\n' "b[01-02]"
  b01
  b02

  % ./formattedrange.py -d $'\t' "b[01-02]"
  b01\tb02

  NOTE: $'\n' is the newline character, $'\t' is the tab character

* Multiple strings can be given as input:
  % ./formattedrange.py "b[1-2,4]" "c[01-02]"
  b1 b2 b4 c01 c02

* You can also pass input strings as stdin with a pipe:
  % echo "b[1-2,4]" | ./formattedrange.py -
  b1 b2 b4
"""
import sys
import os
import re
import getopt

myself = os.path.basename(sys.argv[0])

usage_msg = 'Usage: ' + myself + ' [options...] <string formatted range>' + """
Options:
 -h/--help                This help text
 -d/--delimiter <char>    Use the given characters as line delimiter
 -f/--format <str>        Specify a date range with given standard date format
 -s/--sort                Sort the results and remove overlapping ranges

 Using '-' as last option means read from stdin
"""


def str_numrange_to_list(x):
    """
    Converts a string like '1,2,5-7,10' into a list [1, 2, 5, 6, 7, 10]
    """
    result = []
    for part in x.split(','):
        if '-' in part:
            a, b = part.split('-')
            a, b = int(a), int(b)
            result.extend(range(a, b + 1))
        else:
            a = int(part)
            result.append(a)
    return result

"""
# Another way to do the same thing with list comprehensions:
def str_numrange_to_list(x):
    return sum(((range(*[int(j) + k for k, j in enumerate(i.split('-'))])
        if '-' in i else [int(i)]) for i in x.split(',')), [])
"""


class FormattedRange(object):
    """
    A class which knows how to parse a formatted range string and
    return it as a list of strings.
    """

    my_regexp = re.compile('(.*)\[(\d+)\-(\d+)\](.*)')
    my_regexp2 = re.compile('(.*)\[(.*)\](.*)')

    def __init__(self, s, sep=None, sort=False):
        self._s = s
        self._hascomma = ',' in self._s
        self._formatted = False
        self._extended = None
        self._sorted = None
        self._found = None
        self._begin = None
        self._end = None
        self._msg = "%s%d%s"
        self._sep = sep or ' '
        self._sort = sort
        if not self._hascomma:
            self._found = self.my_regexp.match(self._s)
        else:
            self._found = self.my_regexp2.match(self._s)

        self._setup()

    def _get_range(self):
        if self._found.group(2).startswith('0'):
            self._formatted = True
        if not self._hascomma:
            self._res = self._found.group(2)
            return (xrange(int(self._found.group(2)),
                         int(self._found.group(3)) + 1), 4)
        else:
            self._res = self._found.group(2).split(',')[0]
            if '-' in self._res:
                self._res = self._res.split('-')[0]
            return (str_numrange_to_list(self._found.group(2)), 3)

    def _setup(self):
        if self._found is None:
            return
        self._begin = self._found.group(1)
        self._extended, i = self._get_range()
        self._end = self._found.group(i)

    def get(self):
        if self._found is None:
            return [self._s]

        if self._formatted:
            # Use X digits formatting
            self._msg = "%s%0" + str(len(self._res)) + "d%s"

        ret = []
        if self._sort:
            # Remove overlapping ranges
            # Doing this will use more memory and expand the generator
            # into a set with unique items and than convert the set to a list
            self._sorted = list(set(self._extended[:]))
            self._sorted.sort()
            ls = self._sorted
        else:
            ls = self._extended
        for i in ls:
            ret.append(self._msg % (self._begin, i, self._end))
        return ret

    def __str__(self):
        return self._sep.join(self.get())


class FormattedDateRange(FormattedRange):
    """
    A class which knows how to parse a datetime range and return it as a list
    of strings
    """
    def __init__(self, s, date_format="%Y%m%d", sep=None, sort=False):
        self._date_format = date_format
        FormattedRange.__init__(self, s, sep=sep, sort=sort)
        self._msg = "%s%s%s"

    def _get_range(self):
        from dateutil import parser, rrule
        self._formatted = False
        self._res = self._found.group(2)
        d1 = parser.parse(self._found.group(2))
        d2 = parser.parse(self._found.group(3))
        r = rrule.rrule(rrule.DAILY, dtstart=d1, until=d2)
        return ([i.strftime(self._date_format) for i in r], 4)

    def get(self):
        if self._found is None:
            return [self._s]
        ls = self._extended
        ret = []
        for i in ls:
            ret.append(self._msg % (self._begin, i, self._end))
        return ret


def main(args=None):
    delim = ' '
    format_opt = None
    sort = False

    if len(sys.argv) == 1:
        sys.stderr.write("Error: " + myself + " needs at least one argument\n")
        sys.stderr.write(usage_msg)
        return 2

    cliargs = args or sys.argv[1:]

    opts = None
    remainder = None
    try:
        opts, remainder = getopt.getopt(cliargs, "hsd:f:",
                                ['help', 'sort', 'delimiter=', 'format='])
    except getopt.GetoptError, err:
        sys.stderr.write("Error: %s\n" % err)
        sys.stderr.write(usage_msg)
        return 2

    for o, a in opts:
        if o in ('-h', '--help'):
            sys.stdout.write(usage_msg)
            sys.exit()
        elif o in ('-d', '--delimiter'):
            delim = a
        elif o in ('-f', '--format'):
            format_opt = a
        elif o in ('-s', '--sort'):
            sort = True

    # To use stdin to input cmd use '-' (to use in cmd pipes)
    if '-' in cliargs:
        remainder = [sys.stdin.read()]

    errmsg = " needs at least one string with numerical range as input"
    if not remainder:
        sys.stderr.write("Error: " + myself + errmsg + "\n")
        sys.stderr.write(usage_msg)
        return 1

    for n, i in enumerate(remainder):
        if format_opt is None:
            sys.stdout.write(str(FormattedRange(i, sep=delim, sort=sort)))
        else:
            sys.stdout.write(str(FormattedDateRange(i, date_format=format_opt,
                                                    sep=delim, sort=sort)))
        if n < len(remainder) - 1:
            sys.stdout.write(delim)
        else:
            sys.stdout.write('\n')

if __name__ == "__main__":
    sys.exit(main())
