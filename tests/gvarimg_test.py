import unittest
from noaaclass import noaaclass


class TestGvarimg(unittest.TestCase):
    def setUp(self):
        self.gvar_img = noaaclass.connect('noaa.gvarim', 'noaaadmin').gvar_img

    def test_subscribe(self):
        print self.gvar_img.subscribe.list

    def test_order(self):
        pass


if __name__ == '__main__':
    unittest.main()
