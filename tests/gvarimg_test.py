import unittest
from noaaclass import noaaclass
from datetime import datetime
import time


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
             'start': datetime(2014, 9, 16, 10, 0, 0),
             'end': datetime(2014, 9, 16, 17, 59, 59)
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
             'start': datetime(2014, 9, 2, 10, 0, 0),
             'end': datetime(2014, 9, 3, 17, 59, 59)
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
        gvar_img = self.noaa.subscribe.gvar_img
        auto = lambda x: '[auto]' in x['name']
        data = filter(auto, gvar_img.get())
        self.assertEquals(data, [])

    def test_subscribe_get(self):
        gvar_img = self.noaa.subscribe.gvar_img
        gvar_img.set(self.sub_data)
        data = gvar_img.get(append_files=True)
        for subscription in data:
            for key in ['id', 'enabled', 'name', 'coverage', 'schedule',
                        'south', 'north', 'west', 'east', 'satellite',
                        'format', 'orders']:
                self.assertIn(key, subscription.keys())

    def test_subscribe_set_new_elements(self):
        gvar_img = self.noaa.subscribe.gvar_img
        copy = gvar_img.set(self.sub_data)
        self.assertGreaterEqual(len(copy), len(self.sub_data))
        [self.assertIn(k, copy[i].keys())
         for i in range(len(self.sub_data)) for k in self.sub_data[i].keys()]
        [self.assertEquals(copy[i][k], v)
         for i in range(len(self.sub_data))
         for k, v in self.sub_data[i].items()
         if k is not 'id']

    def test_subscribe_set_edit_elements(self):
        gvar_img = self.noaa.subscribe.gvar_img
        copy = gvar_img.set(self.sub_data)
        self.assertGreaterEqual(len(copy), 2)
        copy[0]['name'] = '[auto] name changed'
        copy[1]['channel'] = [4, 5]
        gvar_img.set(copy)
        edited = gvar_img.get()
        self.assertEquals(edited[0]['name'], copy[0]['name'])
        self.assertEquals(edited[1]['channel'], copy[1]['channel'])

    def test_subscribe_set_remove_element(self):
        gvar_img = self.noaa.subscribe.gvar_img
        copy = gvar_img.set(self.sub_data, async=True)
        self.assertEquals(gvar_img.get(), copy)
        criteria = lambda x: 'sample1' not in x['name']
        copy = filter(criteria, copy)
        gvar_img.set(copy)
        self.assertEquals(gvar_img.get(), copy)

    def test_request_get(self):
        gvar_img = self.noaa.request.gvar_img
        for order in gvar_img.get():
            for key in ['id', 'delivered', 'datetime', 'format', 'files',
                        'south', 'north', 'west', 'east']:
                self.assertIn(key, order.keys())

    def assertEqualsRequests(self, obtained, original):
        asymetric = lambda x: x not in ['coverage', 'end', 'start',
                                        'satellite', 'schedule', 'id']
        for k in filter(asymetric, original.keys()):
            self.assertTrue(k in obtained.keys())
            if isinstance(original[k], float):
                self.assertEqual(int(obtained[k]), int(original[k]))
            elif isinstance(original[k], datetime):
                self.assertEqual(obtained[k].toordinal(),
                                 original[k].toordinal())
            else:
                self.assertEquals(obtained[k], original[k])

    def no_test_request_set_new(self):
        time.sleep(40)
        gvar_img = self.noaa.request.gvar_img
        data = gvar_img.get(async=True)
        data.extend(self.req_data)
        copy = gvar_img.set(data, async=True)
        self.assertEquals(len(copy), len(data))
        [self.assertEqualsRequests(copy[i], data[i])
         for i in range(len(data))]
        time.sleep(40)

if __name__ == '__main__':
    unittest.main()
