#!/usr/bin/env python
# -*- coding: utf-8 -*-
import unittest

from noaaclass import core, noaaclass


class TestCore(unittest.TestCase):
    def setUp(self):
        self.noaa = noaaclass.connect('noaaclass.t', 'noaaclassadmin')

    def test_initialize(self):
        # Check if raise an Exception when the api don't define the initialize.
        with self.assertRaisesRegex(Exception, 'Unregistered API.'):
            core.api('nothing')


if __name__ == '__main__':
    unittest.main()
