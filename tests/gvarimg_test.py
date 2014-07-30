import unittest
from noaaclass import noaaclass


class TestGvarimg(unittest.TestCase):
    def setUp(self):
        self.noaa = noaaclass.connect('noaa.gvarim', 'noaaadmin')

    def test_subscribe(self):
        self.gvar_img = self.noaa.subscribe.gvar_img
        print self.gvar_img.get()

    def test_request(self):
        self.gvar_img = self.noaa.request.gvar_img
        print self.gvar_img.get()


if __name__ == '__main__':
    unittest.main()
