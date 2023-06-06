"""A module that tests doctests.

There are 3 different levels of a verbosity parameter:
0 (quiet): you just get the total numbers of tests executed and the global
result.
1 (default): you get the same plus a dot for every successful test or a F for
every failure.
2 (verbose): you get the help string of every test and the result.
"""

import doctest
import unittest

from django.test import TestCase

from ships import utils


class DoctestTestCase(TestCase):
    def test_utils_doctests(self):
        test_suit = unittest.TestSuite()
        test_suit.addTest(doctest.DocTestSuite(utils))
        runner = unittest.TextTestRunner(verbosity=2).run(test_suit)

        assert not runner.failures
