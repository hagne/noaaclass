import unittest
from noaaclass import noaaclass
from noaaclass import core
from datetime import datetime


class TestNoaaclass(unittest.TestCase):
    def setUp(self):
        self.noaa = noaaclass.connect('noaaclass.t', 'noaaclassadmin')

    def test_last_response_setter(self):
        # It should raise an exception if the response was wrong.
        with self.assertRaisesRegexp(Exception, 'Connection error \(500\)'):
            self.noaa.get('wrong_page')
        # If the page was valid it should change the last_response value.
        previous_response = self.noaa.last_response
        self.noaa.get('welcome')
        self.assertNotEquals(self.noaa.last_response, previous_response)

    def test_next_up_datetime(self):
        # Should return an UTC time between the start and the end.
        from pytz import utc
        start = datetime.utcnow().replace(tzinfo=utc)
        time = noaaclass.next_up_datetime()
        end = datetime.utcnow().replace(tzinfo=utc)
        self.assertTrue(start <= time <= end)

    def test_login(self):
        # Check if the connection login was succsessful.
        self.assertTrue(self.noaa.signed_in)

    def test_login_failure(self):
        # Check if the connection fails with an unregistered user/pass.
        with self.assertRaisesRegexp(Exception,
                                     'unregistered: Invalid NOAA user '
                                     'or wrong password.'):
            noaaclass.connect('unregistered', 'nil')

    def test_an_existent_module(self):
        # Check if an existent module is loadad dinamically.
        self.assertEquals(self.noaa.request.__class__.__bases__[0],
                          core.Action)
        self.assertEquals(self.noaa.subscribe.__class__.__bases__[0],
                          core.Action)

    def test_non_existent_module(self):
        # Check if the program raise an Exception if the module not exists.
        with self.assertRaisesRegexp(Exception,
                                     'There is no API to '
                                     'the "innexistent" product.'):
            self.noaa.request.innexistent

    def test_products(self):
        # Check if the api list is consistent with the supported ones.
        self.assertEquals(self.noaa.request.products(), [u'gvar_img'])
        self.assertEquals(self.noaa.subscribe.products(), [u'gvar_img'])


if __name__ == '__main__':
    unittest.main()
