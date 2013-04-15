import unittest
from nose.tools import eq_
from formattedrange import FormattedRange, FormattedDateRange, main
from StringIO import StringIO
from mock import __version__ as mock_ver
assert int(mock_ver.split('.')[0]) >= 1, "mock version: %s <= 1.0 " % mock_ver
from mock import patch

class TestFormattedrange(unittest.TestCase):

    def setUp(self):
        self._max = 10

    def test_range_normal(self):
        fr = FormattedRange("a[1-%s]b" % self._max)
        for n, i in enumerate(fr.get()):
            eq_(i, "a%db" % (n + 1))
        

    def test_range_formatted(self):
        # Use 2 digits numbers formatting
        fr = FormattedRange("a[01-%s]b" % self._max)
        for n, i in enumerate(fr.get()):
            eq_(i, "a%02db" % (n + 1))


class TestFormattedDateRange(unittest.TestCase):

    def test_date_range(self):
        fr = FormattedDateRange("a[20120228-20120301]b")
        expected = ["20120228", "20120229", "20120301"]
        for n, i in enumerate(fr.get()):
            eq_(i, "a%sb" % expected[n])


class TestCliOptions(unittest.TestCase):

    def test_main_standard(self):
        args = ['a[1-2]b']
        eq_(main(args), 0)

    @patch('sys.stdout', new_callable=StringIO)
    def test_main_w_options(self, mock_stdout):
        args = ['a[1-2]b']
        main(args)
        eq_(mock_stdout.getvalue(), 'a1b a2b\n')


