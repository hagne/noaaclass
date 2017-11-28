#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import unittest
from datetime import datetime
from types import MethodType as OriginalMethodType

from requests.exceptions import ConnectionError

from noaaclass import core, noaaclass

if sys.version_info[0] == 2:
    # noinspection PyArgumentList
    def MethodType(function, instance):
        return OriginalMethodType(function, instance, instance.__class__)
else:
    MethodType = OriginalMethodType


def fake_get(self, url, proto='https'):
    """Define the fake get method."""
    if 'classlogin' in url:
        raise ConnectionError('Forced error.')


class TestNoaaclass(unittest.TestCase):
    def setUp(self):
        self.noaa = noaaclass.connect('noaaclass.t', 'noaaclassadmin')

    def test_load_home_page(self):
        # PATCHED: It replace temporally the get method.
        self.noaa.get = MethodType(fake_get, self.noaa)

        # Check if raise an Exception when can't load the main page.
        with self.assertRaisesRegex(Exception, 'NOAA CLASS is down until'):
            self.noaa.authenticate.load_home_page(self.noaa)

    def test_last_response_setter(self):
        # Check if raise an exception if the response was wrong.
        with self.assertRaisesRegex(Exception, 'Connection error \(200\)'):
            self.noaa.get('wrong_page')

        # Check if the page was valid it should change the last_response value.
        previous_response = self.noaa.last_response
        self.noaa.get('welcome')
        self.assertNotEqual(self.noaa.last_response, previous_response)

    def test_next_up_datetime(self):
        # Check if return an UTC time between the start and the end.
        from pytz import utc
        start = datetime.utcnow().replace(tzinfo=utc)
        time = noaaclass.next_up_datetime()
        end = datetime.utcnow().replace(tzinfo=utc)
        self.assertTrue(start <= time <= end)

    def test_login(self):
        # Check if the connection login was successful.
        self.assertTrue(self.noaa.signed_in)

    def test_login_failure(self):
        # Check if the connection fails with an unregistered user/pass.
        with self.assertRaisesRegex(Exception,
                                    'unregistered: Invalid NOAA user '
                                    'or wrong password.'):
            noaaclass.connect('unregistered', 'nil')

    def test_an_existent_module(self):
        # Check if an existent module is loaded dinamically.
        self.assertEqual(self.noaa.request.__class__.__bases__[0],
                         core.Action)
        self.assertEqual(self.noaa.subscribe.__class__.__bases__[0],
                         core.Action)

    def test_non_existent_module(self):
        # Check if the program raise an Exception if the module not exists.
        with self.assertRaisesRegex(Exception,
                                    'There is no API to '
                                    'the "inexistent" product.'):
            self.noaa.request.innexistent

    def test_products(self):
        # Check if the api list is consistent with the supported ones.
        self.assertEqual(self.noaa.request.products(), ['gvar_img', 'viirs_sdr'])
        self.assertEqual(self.noaa.subscribe.products(), ['gvar_img', 'viirs_sdr'])


if __name__ == '__main__':
    unittest.main()
