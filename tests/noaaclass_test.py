import unittest
from noaaclass import noaaclass
from noaaclass import core


class TestNoaaclass(unittest.TestCase):
    def setUp(self):
        self.noaa = noaaclass.connect('noaa.gvarim', 'noaaadmin')

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
        self.assertEquals(self.noaa.gvar_img.__class__.__bases__[0], core.api)

    def test_non_existent_module(self):
        # Check if the program raise an Exception if the module not exists.
        with self.assertRaisesRegexp(Exception,
                                     'There is no API to '
                                     'the "innexistent" product.'):
            self.noaa.innexistent

    def test_products(self):
        # Check if the api list is consistent with the supported ones.
        self.assertEquals(self.noaa.products(), [u'gvar_img'])


if __name__ == '__main__':
    unittest.main()
