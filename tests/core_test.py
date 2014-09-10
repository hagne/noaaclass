import unittest
from noaaclass import noaaclass
from noaaclass import core


class TestCore(unittest.TestCase):
    def setUp(self):
        self.noaa = noaaclass.connect('noaaclass.t', 'noaaclassadmin')

    def test_initialize(self):
        # Check if raise an Exception when the api don't define the initialize.
        with self.assertRaisesRegexp(Exception, 'Unregistered API.'):
                core.api('nothing')

if __name__ == '__main__':
    unittest.main()
