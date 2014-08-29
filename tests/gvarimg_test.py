import unittest
from noaaclass import noaaclass
from copy import deepcopy
from datetime import datetime


class TestGvarimg(unittest.TestCase):
    def remove_all_in_server(self):
        sub_data = self.noaa.subscribe.gvar_img.get()
        ids = [d['id'] for d in sub_data]
        if len(ids):
            self.noaa.get('sub_delete?actionbox=%s' % '&actionbox='.join(ids))

    def setUp(self):
        self.noaa = noaaclass.connect('noaaclass.t', 'noaaclassadmin')
        self.sub_data = [
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
        self.req_data = deepcopy(self.sub_data)
        self.req_data[0].update({
            'start': datetime(2014, 7, 23, 0, 0, 0),
            'end': datetime(2014, 7, 23, 23, 59, 59)
        })
        self.req_data[1].update({
            'start': datetime(2014, 7, 20, 0, 0, 0),
            'end': datetime(2014, 7, 20, 23, 59, 59)
        })
        self.remove_all_in_server()

    def tearDown(self):
        self.remove_all_in_server()

    def test_subscribe_get_empty(self):
        self.gvar_img = self.noaa.subscribe.gvar_img
        self.assertEquals(self.gvar_img.get(), [])

    def test_subscribe_get(self):
        self.gvar_img = self.noaa.subscribe.gvar_img
        for order in self.gvar_img.get():
            for key in ['id', 'enabled', 'name', 'coverage', 'schedule',
                        'south', 'north', 'west', 'east', 'satellite',
                        'format']:
                self.assertIn(key, order.keys())

    def test_subscribe_set_new_elements(self):
        self.gvar_img = self.noaa.subscribe.gvar_img
        copy = self.gvar_img.set(self.sub_data)
        self.assertEquals(len(copy), 2)
        sort = sorted
        [self.assertEquals(sort(copy[i].keys()), sort(self.sub_data[i].keys()))
         for i in range(len(self.sub_data))]
        [self.assertEquals(copy[i][k], v)
         for i in range(len(self.sub_data))
         for k, v in self.sub_data[i].items()
         if k is not 'id']

    def test_subscribe_set_edit_elements(self):
        self.gvar_img = self.noaa.subscribe.gvar_img
        copy = self.gvar_img.set(self.sub_data)
        self.assertEquals(len(copy), 2)
        copy[0]['name'] = '[auto] name changed'
        copy[1]['channel'] = [4, 5]
        self.gvar_img.set(copy)
        edited = self.gvar_img.get()
        self.assertEquals(edited[0]['name'], copy[0]['name'])
        self.assertEquals(edited[1]['channel'], copy[1]['channel'])

    def test_subscribe_set_remove_element(self):
        self.gvar_img = self.noaa.subscribe.gvar_img
        copy = self.gvar_img.set(self.sub_data)
        self.assertEquals(self.gvar_img.get(), copy)
        copy.pop(0)
        self.gvar_img.set(copy)
        self.assertEquals(self.gvar_img.get(), copy)

    def test_request_get(self):
        self.gvar_img = self.noaa.request.gvar_img
        for order in self.gvar_img.get():
            for key in ['id', 'delivered', 'datetime', 'format', 'files',
                        'south', 'north', 'west', 'east']:
                self.assertIn(key, order.keys())


if __name__ == '__main__':
    unittest.main()
