import unittest
from noaaclass import noaaclass


class TestGvarimg(unittest.TestCase):
    def setUp(self):
        self.noaa = noaaclass.connect('noaaclass.t', 'noaaclassadmin')

    def test_subscribe_get(self):
        self.gvar_img = self.noaa.subscribe.gvar_img
        self.assertEquals(self.gvar_img.get(), {})

    def test_request(self):
        self.gvar_img = self.noaa.request.gvar_img
        self.assertEquals(self.gvar_img.get(), {})


if __name__ == '__main__':
    unittest.main()
