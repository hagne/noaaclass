import unittest
from noaaclass import noaaclass
from datetime import datetime


class TestGvarimg(unittest.TestCase):
    def remove_all_in_server(self):
        sub_data = self.noaa.subscribe.gvar_img.get()
        ids = [d['id'] for d in sub_data if '[auto]' in d['name']]
        if len(ids):
            self.noaa.get('sub_delete?actionbox=%s' % '&actionbox='.join(ids))

    def init_subscribe_data(self):
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
            {'id': '+',
             'enabled': True,
             'name': 'static',
             'north': -26.73,
             'south': -33.52,
             'west': -61.06,
             'east': -48.51,
             'coverage': ['SH'],
             'schedule': ['R'],
             'satellite': ['G13'],
             'channel': [1],
             'format': 'NetCDF',
             },
        ]
        old_data = self.noaa.subscribe.gvar_img.get()
        names = [d['name'] for d in self.sub_data]
        self.sub_data.extend(filter(lambda x: x['name'] not in names,
                                    old_data))

    def init_request_data(self):
        self.req_data = [
            {'id': '+',
             'north': -26.72,
             'south': -43.59,
             'west': -71.02,
             'east': -48.52,
             'coverage': ['SH'],
             'schedule': ['R'],
             'satellite': ['G13'],
             'channel': [1],
             'format': 'NetCDF',
             'start': datetime(2014, 9, 3, 0, 0, 0),
             'end': datetime(2014, 9, 4, 23, 59, 59)
             },
            {'id': '+',
             'north': -26.73,
             'south': -43.52,
             'west': -71.06,
             'east': -48.51,
             'coverage': ['SH'],
             'schedule': ['R'],
             'satellite': ['G13'],
             'channel': [2],
             'format': 'NetCDF',
             'start': datetime(2014, 9, 2, 0, 0, 0),
             'end': datetime(2014, 9, 3, 23, 59, 59)
             },
        ]

    def setUp(self):
        self.noaa = noaaclass.connect('noaaclass.t', 'noaaclassadmin')
        self.init_subscribe_data()
        self.init_request_data()
        self.remove_all_in_server()

    def tearDown(self):
        self.remove_all_in_server()

    def test_subscribe_get_empty(self):
        self.gvar_img = self.noaa.subscribe.gvar_img
        auto = lambda x: '[auto]' in x['name']
        data = filter(auto, self.gvar_img.get())
        self.assertEquals(data, [])

    def test_subscribe_get(self):
        self.gvar_img = self.noaa.subscribe.gvar_img
        self.gvar_img.set(self.sub_data)
        for order in self.gvar_img.get():
            for key in ['id', 'enabled', 'name', 'coverage', 'schedule',
                        'south', 'north', 'west', 'east', 'satellite',
                        'format']:
                self.assertIn(key, order.keys())

    def test_subscribe_set_new_elements(self):
        self.gvar_img = self.noaa.subscribe.gvar_img
        copy = self.gvar_img.set(self.sub_data)
        self.assertGreaterEqual(len(copy), len(self.sub_data))
        [self.assertIn(k, copy[i].keys())
         for i in range(len(self.sub_data)) for k in self.sub_data[i].keys()]
        [self.assertEquals(copy[i][k], v)
         for i in range(len(self.sub_data))
         for k, v in self.sub_data[i].items()
         if k is not 'id']

    def test_subscribe_set_edit_elements(self):
        self.gvar_img = self.noaa.subscribe.gvar_img
        copy = self.gvar_img.set(self.sub_data)
        self.assertGreaterEqual(len(copy), 2)
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
        criteria = lambda x: 'sample1' not in x['name']
        copy = filter(criteria, copy)
        self.gvar_img.set(copy)
        self.assertEquals(self.gvar_img.get(), copy)

    def test_request_get(self):
        self.gvar_img = self.noaa.request.gvar_img
        for order in self.gvar_img.get():
            for key in ['id', 'delivered', 'datetime', 'format', 'files',
                        'south', 'north', 'west', 'east']:
                self.assertIn(key, order.keys())

    def test_request_set_new(self):
        """self.gvar_img = self.noaa.request.gvar_img
        copy = self.gvar_img.set(self.req_data)
        self.assertEquals(len(copy), 2)
        sort = sorted
        [self.assertEquals(sort(copy[i].keys()), sort(self.req_data[i].keys()))
         for i in range(len(self.req_data))]
        [self.assertEquals(copy[i][k], v)
         for i in range(len(self.req_data))
         for k, v in self.req_data[i].items()
         if k is not 'id']
        """
        pass

if __name__ == '__main__':
    unittest.main()
