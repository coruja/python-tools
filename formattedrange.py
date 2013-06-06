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
import itertools

myself = os.path.basename(sys.argv[0])

usage_msg = 'Usage: ' + myself + ' [options...] <string formatted range>' + """
Options:
 -h/--help                This help text
 -d/--delimiter <char>    Use the given characters as line delimiter
 -f/--format <str>        Specify a date range with given standard date format
 -s/--sort                Sort the results and remove overlapping ranges

 Using '-' as last option means read from stdin
"""

def usage(msg=None):
    s = None
    err = 0
    if msg and msg.startswith("Error:"):
        s = sys.stderr
        err = 1
    else:
        s = sys.stdout
    if msg and s:
        s.write(msg + "\n")
    sys.stdout.write(usage_msg)
    return err

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


class FormattedRangeError(Exception):
    pass


class FormattedRange(object):
    """
    A class which knows how to parse a formatted range string and
    return it as a list of strings.
    """

    my_regexp = re.compile("([^\[\]]*)(\[[^\[\]]*\])([^\[\]]*)")
    my_regexp2 = re.compile('(\d+)\-(\d+)')

    def __init__(self, s, sep=None, sort=False):
        self._s = s
        self._sep = sep or ' '
        self._sort = sort
        self._msg = "%s%d%s"
        self._zfill = 0

        self._hascomma = False
        self._formatted = False

        self._int_ls = []
        self._setup()

    def _setup(self):
        # a[01-02]b[01-10]c -> [('a', '[01-02]', 'b'), ('', '[01-10]', 'c')]
        found = self.my_regexp.findall(self._s) or []
        for n in found:
            self._begin, self._extended, self._end = n[0], self._get_range(n[1]), n[2]
            self._int_ls.append((self._begin, self._extended, self._end))

    def _get_range(self, range_str):
        range_str = range_str.replace('[', '').replace(']', '')
        if range_str.startswith('0'):
            self._formatted = True
        found = self.my_regexp2.search(range_str)
        if found:
            self._zfill = len(found.group(1))
            if ',' not in range_str:
                return range(int(found.group(1)), int(found.group(2)) + 1)
            else:
                return str_numrange_to_list(range_str)
        else:
            raise FormattedRangeError("Could not parse range string")

    def get(self):
        if not self._int_ls:
            return [self._s]

        if self._formatted:
            # Use X digits formatting
            self._msg = "%s%0" + str(self._zfill) + "d%s"

        expanded = [None] * len(self._int_ls)
        i = 0
        for n, (b, r, e) in enumerate(self._int_ls):
            expanded[n] = []
            for el in r:
                msg = self._msg % (b, el, e)
                expanded[n].append(msg)

        ret = []
        for element in itertools.product(*expanded):
            ret.append(''.join(element))

        return ret

    def __str__(self):
        return self._sep.join(self.get())


class FormattedDateRangeError(Exception):
    pass


class FormattedDateRange(FormattedRange):
    """
    A class which knows how to parse a datetime range and return it as a list
    of strings
    """
    def __init__(self, s, date_format="%Y%m%d", sep=None, sort=False):
        self._date_format = date_format
        FormattedRange.__init__(self, s, sep=sep, sort=sort)
        self._msg = "%s%s%s"

    def _get_range(self, range_str):
        range_str = range_str.replace('[', '').replace(']', '')
        from dateutil import parser, rrule
        self._formatted = False
        found = self.my_regexp2.search(range_str)
        if found:
            try:
                d1 = parser.parse(found.group(1))
                d2 = parser.parse(found.group(2))
                r = rrule.rrule(rrule.DAILY, dtstart=d1, until=d2)
            except ValueError, e:
                raise FormattedDateRangeError(e)
            return [i.strftime(self._date_format) for i in r]
        else:
            raise FormattedDateRangeError("Could not parse range string")

    def get(self):
        if not self._int_ls:
            return [self._s]
        ls = self._extended
        ret = []
        for i in ls:
            ret.append(self._msg % (self._begin, i, self._end))
        return ret


def main(args=None):
    """ The main function of this script
    returns 0 on success or 1 otherwise
    """
    delim = ' '
    format_opt = None
    sort = False

    cliargs = args or sys.argv[1:]

    if cliargs and len(cliargs) == 0:
        return usage("Error:" + myself + " needs at least one argument")

    opts = None
    remainder = None
    try:
        opts, remainder = getopt.getopt(cliargs, "hsd:f:",
                                ['help', 'sort', 'delimiter=', 'format='])
    except getopt.GetoptError, err:
        return usage("Error: %s" % err)

    for o, a in opts:
        if o in ('-h', '--help'):
            return usage()
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
        return usage("Error: " + myself + errmsg)

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

    return 0

if __name__ == "__main__":
    sys.exit(main())
