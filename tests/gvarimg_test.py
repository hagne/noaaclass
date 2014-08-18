import unittest
from noaaclass import noaaclass


class TestGvarimg(unittest.TestCase):
    def remove_all_in_server(self):
        data = self.noaa.subscribe.gvar_img.get()
        ids = [d['id'] for d in data]
        if len(ids):
            self.noaa.get('sub_delete?actionbox=%s' % '&actionbox='.join(ids))

    def setUp(self):
        self.noaa = noaaclass.connect('noaaclass.t', 'noaaclassadmin')
        self.data = [
            {'id': '+',
             'enabled': True,
             'name': '[auto] sample1',
             'north': -26.72,
             'south': -43.59,
             'west': -71.02,
             'east': -48.52,
             'coverage': ['SH'],
             'schedule': ['R'],
             'satellite': ['G13'],
             'channel': [1],
             'format': 'NetCDF',
             },
            {'id': '+',
             'enabled': False,
             'name': '[auto] sample2',
             'north': -26.73,
             'south': -43.52,
             'west': -71.06,
             'east': -48.51,
             'coverage': ['SH'],
             'schedule': ['R'],
             'satellite': ['G13'],
             'channel': [2],
             'format': 'NetCDF',
             },
        ]
        self.remove_all_in_server()
        # TODO: Multiple selection on satellite, coverage, schedule, channel

    def tearDown(self):
        # self.remove_all_in_server()
        pass

    def test_subscribe_get_empty(self):
        self.gvar_img = self.noaa.subscribe.gvar_img
        self.assertEquals(self.gvar_img.get(), [])

    def test_subscribe_set_new_elements(self):
        self.gvar_img = self.noaa.subscribe.gvar_img
        result = self.gvar_img.set(self.data)
        self.assertEquals(len(result), 2)
        sort = sorted
        [self.assertEquals(sort(result[i].keys()), sort(self.data[i].keys()))
         for i in range(len(self.data))]
        [self.assertEquals(result[i][k], v)
         for i in range(len(self.data)) for k, v in self.data[i].items()
         if k is not 'id']

    def test_subscribe_set_edit_elements(self):
        pass

    def test_subscribe_set_remove_element(self):
        pass

    def test_request(self):
        self.gvar_img = self.noaa.request.gvar_img
        self.assertEquals(self.gvar_img.get(), {})


if __name__ == '__main__':
    unittest.main()
