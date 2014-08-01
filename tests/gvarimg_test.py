import unittest
from noaaclass import noaaclass


class TestGvarimg(unittest.TestCase):
    def setUp(self):
        self.noaa = noaaclass.connect('noaaclass.t', 'noaaclassadmin')
        self.data = [
            {'id': '+',
             'enabled': True,
             'north': -26.72,
             'south': -43.59,
             'west': -71.02,
             'east': -48.52,
             'coverage': ['SH'],
             'schedule': ['R'],
             'satellite': ['G13'],
             'channel': [1, 2, 3],
             'format': 'NetCDF',
             },
            {'id': '+',
             'enabled': False,
             'north': -26.72,
             'south': -43.59,
             'west': -71.02,
             'east': -48.52,
             'coverage': ['SH'],
             'schedule': ['R'],
             'satellite': ['G13'],
             'channel': [1, 2, 3],
             'format': 'NetCDF',
             },
        ]

    def test_subscribe_get_empty(self):
        self.gvar_img = self.noaa.subscribe.gvar_img
        self.assertEquals(self.gvar_img.get(), {})

    def test_subscribe_set_new_elements(self):
        self.gvar_img = self.noaa.subscribe.gvar_img
        self.gvar_img.set(self.data)
        result = self.gvar_img.get()
        self.assertEquals(len(result), 2)
        [self.assertEquals(result[k], v) for r in self.data
         for k, v in r.items() if k != 'id']

    def test_subscribe_set_edit_elements(self):
        pass

    def test_subscribe_set_remove_element(self):
        pass

    def test_request(self):
        self.gvar_img = self.noaa.request.gvar_img
        self.assertEquals(self.gvar_img.get(), {})


if __name__ == '__main__':
    unittest.main()
