#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
GOES Satellite Data GVAR_IMG (Imager).

For more info see CLASS Glossary:
https://www.class.ncdc.noaa.gov/glossary/GVAR_IMG.htm
"""

import re
from datetime import datetime, timedelta
from random import randint

from noaaclass import core

select = lambda i, n, data: [d for d in data if d['id'] == i or d['name'] == n]
changed = lambda x, data: x != select(x['id'], x['name'], data)[0]
is_new = lambda e, old_data: (e['id'] is '+'
                              and not select(e['id'], e['name'], old_data))
is_removed = lambda e, data: e['id'] not in [x['id'] for x in data]
need_id = lambda e, old_data: not e['id'].isdigit() and not is_new(e, old_data)
enabled = lambda x: re.match(r'.*%22(.*)%22.*', x).group(1) == 'Y'
element = lambda t, ptrn, idx: t.select(ptrn)[idx].text
file_item = lambda row, i: element(row, 'td', i)
file_data = lambda row: (file_item(row, 3), int(file_item(row, 5)),
                         file_item(row, 4) == 'GVAR_IMG')
resume_id = lambda t: element(t, 'td a', 0)
resume_activity = (lambda t:
                   datetime.strptime(element(t, 'td', -1).split('.')[0],
                                     '%Y-%m-%d %H:%M:%S')
                   if element(t, 'td', -1) else datetime.utcnow())
resume_status = lambda t: element(t, 'td', -3).lower()
resume_size = lambda t: int(element(t, 'td', -4))
resume_order = lambda t: {
    'id': resume_id(t),
    'last_activity': resume_activity(t),
    'status': resume_status(t),
    'size': resume_size(t),
}

FILE_FORMATS = {
    '.nc': 'NetCDF',
    '.area': 'Area',
    '.giff': 'GIF',
    '.jpg': 'JPG',
    '': 'Raw'
}


class Api(core.Api):
    def __init__(self, action):
        super(Api, self).__init__(action)

    def initialize(self):
        self.name = 'GVAR_IMG'
        self.name_upper = self.name.upper()
        direct = lambda x: x
        enabled_to_local = lambda x: x == 'Y'
        enabled_to_remote = lambda x: 'Y' if x else 'N'
        single = lambda x, t: t(x[0])
        multiple = lambda l, t: list(map(t, l))
        self.translate(single, 'enabled', enabled_to_local, 'subhead_sub_enabled', enabled_to_remote)
        self.translate(single, 'name', direct, 'subhead_sub_description', str)
        self.translate(single, 'north', float, 'nlat', str)
        self.translate(single, 'south', float, 'slat', str)
        self.translate(single, 'west', float, 'wlon', str)
        self.translate(single, 'east', float, 'elon', str)
        self.translate(multiple, 'coverage', direct, 'Coverage', direct)
        self.translate(multiple, 'schedule', direct, 'Satellite Schedule', direct)
        self.translate(multiple, 'satellite', direct, 'Satellite', direct)
        self.translate(multiple, 'channel', int, 'chan_%s' % self.name, str)
        self.translate(single, 'format', direct, 'format_%s' % self.name, str)

    def subscribe_get_append_orders(self, noaa, d, append_files, hours, async):
        page = noaa.get('order_list?display_id=%s&order_type=SUBS&'
                        'condense=false&hours=%s&page_number=1&'
                        'group_size=25' % (d['id'], hours))
        d['orders'] = self.initialize_orders(page)
        self.parse_orders(noaa, d['orders'], append_files, hours, async)

    def subscribe_get(self, append_orders=False, append_files=False, hours=2,
                      async=False):
        # If append_files also automatically should append_orders.
        append_orders = append_files or append_orders
        noaa = self.conn
        page = noaa.get('subscriptions')
        data = page.select('.class_table td a')
        data = [{'id': d.text, 'enabled': enabled(d['href'])}
                for d in data if d.text.isdigit()]
        for d in data:
            noaa.get('sub_details?sub_id=%s&enabled=%s'
                     % (d['id'], 'Y' if d['enabled'] else 'N'))
            forms = noaa.translator.get_forms(noaa.last_response_soup)
            tmp = forms['sub_frm']
            noaa.post('sub_deliver', tmp, form_name='sub_frm')
            forms = noaa.translator.get_forms(noaa.last_response_soup)
            join = lambda x, y: dict(list(x.items()) + list(y.items()))
            tmp = join(tmp, forms['sub_frm'])
            d.update(self.post_to_local(tmp))
            if append_orders:
                self.subscribe_get_append_orders(noaa, d, append_files, hours, async)
        return data

    def subscribe_new(self, e):
        self.conn.get('sub_details?sub_id=0&'
                      'datatype_family={}&submit.x={}&submit.y={}'.format(self.name_upper,
                                                                          randint(1, 60),
                                                                          randint(1, 11)))
        data = self.local_to_post(e)
        self.conn.post('sub_deliver', data, form_name='sub_frm')
        channel_mask = list('000000' + 'X' * 24)
        data = self.local_to_post(e)
        for i in e['channel']:
            channel_mask[i - 1] = '1'
        data['channels_%s' % self.name_upper] = ''.join(channel_mask), \
                                                self.conn.post('sub_save', data, form_name='sub_frm')

    def subscribe_edit(self, e):
        data = self.local_to_post(e)
        self.conn.get('sub_details?sub_id=%s&enabled=%s'
                      % (e['id'], data['subhead_sub_enabled']))
        data = self.local_to_post(e)
        self.conn.post('sub_deliver', data, form_name='sub_frm')
        channel_mask = list('000000' + 'X' * 24)
        data = self.local_to_post(e)
        for i in e['channel']:
            channel_mask[i - 1] = '1'
            data['channels_%s' % self.name_upper] = ''.join(channel_mask),
        self.conn.post('sub_save', data, form_name='sub_frm')

    def subscribe_remove(self, e):
        self.conn.get('sub_delete?actionbox=%s' % e['id'])

    def subscribe_classify(self, data, async):
        old_data = self.subscribe_get(append_orders=False, async=async)
        incomplete = [d for d in data if need_id(d, old_data)]
        for d in incomplete:
            d['id'] = select(d['id'], d['name'], old_data)[0]['id']
        remove = [e for e in old_data if is_removed(e, data)]
        new = [e for e in data if is_new(e, old_data)]
        edit = [e for e in data if e not in new and changed(e, old_data)]
        return remove, new, edit

    def subscribe_set(self, data, append_orders=False, async=False):
        remove, new, edit = self.subscribe_classify(data, async)
        list(map(self.subscribe_new, new))
        list(map(self.subscribe_edit, edit))
        list(map(self.subscribe_remove, remove))

    def obtain_items(self, last_response_soup, item_functor, check_functor):
        anchors = last_response_soup.select('.zebra td a')
        return list(map(item_functor, list(filter(check_functor, anchors))))

    def deduce_head(self, noaa, order, last_response_soup):
        rows = last_response_soup.select('.zebra tr')
        rows = [r.select('td.oq_table_line_item_row') for r in rows]
        files = [f for f in [t[1].getText() if t else t for t in rows] if f]
        if 'format' not in order and files[0] != 'Pending':
            extension = re.compile(r'.*BAND\_\d\d(.*)')
            channel = re.compile(r'.*BAND\_(\d+).*')
            exts = [e for e in map(extension.match, files) if e]
            exts = [ext for ext in [ext.group(1) for ext in exts] if ext != '.meta']
            chs = list(map(channel.match, files))
            chs = [ch for ch in [int(ch.group(1)) if ch else None for ch in chs] if ch]
            chs.sort()
            other = {
                'format': FILE_FORMATS[exts[0]] if exts else 'unknown',
                'channel': chs,
            }
            order.update(other)

    def parse_order(self, noaa, order, last_response_soup, append_files):
        table = last_response_soup.select('.class_table td')
        order['datetime'] = datetime.strptime(table[3].text,
                                              '%Y-%m-%d %H:%M:%S')
        order['files'] = {'http': [], 'ftp': []}
        day_before_yesterday = datetime.utcnow() - timedelta(days=2)
        order['old'] = order['datetime'] < day_before_yesterday
        self.deduce_head(noaa, order, last_response_soup)
        if append_files:
            item = lambda i: i['href'].split("'")[1]
            is_http = lambda i: 'www' in i.text
            is_ftp = lambda i: 'ftp' in i.text
            order['files']['http'].extend(
                self.obtain_items(last_response_soup, item, is_http))
            order['files']['ftp'].extend(
                self.obtain_items(last_response_soup, item, is_ftp))

    def parse_orders(self, noaa, orders, append_files, hours, async):
        urls = [('order_details?order_number=%s&hours=%i&page_number=1'
                 '&group_size=1000' % (order['id'], hours))
                for order in orders]
        responses = noaa.getmultiple(urls, async=async)
        list(map(lambda a, noaa=noaa, append_files=append_files:
                 self.parse_order(noaa, a[0], a[1], append_files),
                 list(zip(orders, responses))))

    def initialize_orders(self, page):
        # Filter old or unused data
        data = page.select('.zebra tr')
        data = [t for t in data if len(t.select('td')) > 0]
        return [o for o in map(resume_order, data) if o['status'] != 'delivered']

    def request_get(self, append_files=False, hours=2, async=False):
        noaa = self.conn
        page = noaa.get('order_list?order=&status=&type=USER'
                        '&displayDetails=N&hours=%i&status_page=1'
                        '&large_status=&group_size=1000&orderby=1' %
                        hours)
        orders = self.initialize_orders(page)
        self.parse_orders(noaa, orders, append_files, hours, async)
        key = lambda x: str(x['id'])
        orders.sort(key=key)
        return orders

    def request_new(self, e):
        noaa = self.conn
        noaa.get('search?sub_id=0&datatype_family={}&submit.x={}&submit.y={}'.format(self.name_upper,
                                                                                     randint(1, 60),
                                                                                     randint(1, 11)))
        data = self.local_to_post(e)
        data['start_date'] = e['start'].strftime('%Y-%m-%d')
        data['start_time'] = e['start'].strftime('%H:%M:%S')
        data['end_date'] = e['end'].strftime('%Y-%m-%d')
        data['end_time'] = e['end'].strftime('%H:%M:%S')
        data['data_start'] = '1993-09-01'
        data['data_end'] = datetime.utcnow().strftime('%Y-%m-%d')
        data['dsname_pattern'] = "^GOES\d\d\.(19|20)\d\d\.[0123]\d\d(.{0,15})$"
        data['between_through'] = 'T'
        noaa.post('psearch%s' % self.name_upper, data=data, form_name='search_frm')
        # It iterate over the pages to select the items of each page.
        page = 0
        lapse = timedelta(hours=0)
        while e['start'] + lapse <= e['end']:
            forms = noaa.translator.get_forms(noaa.last_response_soup)
            tab = e['start'] + lapse
            tmp = forms['rform']
            tmp['update_action'] = 'GotoInterval'
            tmp['GotoInterval'] = tab.strftime('%Y-%m-%d %H:%M:%S.000')
            tmp['page'] = page
            noaa.post('results%s' % self.name, data=tmp, form_name='rform')
            forms = noaa.translator.get_forms(noaa.last_response_soup)
            tmp = forms['rform']
            tmp['update_action'] = 'Select Page'
            tmp['GotoInterval'] = tab.strftime('%Y-%m-%d %H:%M:%S.000')
            tmp['page'] = page
            noaa.post('results%s' % self.name, data=tmp, form_name='rform')
            page += 1
            lapse += timedelta(hours=6)
        forms = noaa.translator.get_forms(noaa.last_response_soup)
        tmp = forms['rform']
        forms = noaa.translator.get_forms(noaa.last_response_soup)
        noaa.get('shopping_cart')
        forms = noaa.translator.get_forms(noaa.last_response_soup)
        tmp = forms['shop']
        trans = (lambda k, v, e: [e['format']] if 'format' in k else (e['channel'] if 'channel' in k else v))
        tmp = {k: trans(k, v, e) for k, v in list(tmp.items())}
        tmp['cocoon-action'] = ['PlaceOrder']
        self.conn.post('shop', data=tmp, form_name='shop')
        forms = noaa.translator.get_forms(noaa.last_response_soup)
        tmp = forms['FORM1']
        tmp['purpose'] = ['education']
        tmp['postSurvey'] = ['Submit']
        self.conn.post('survey', data=tmp, form_name='FORM1')

    def request_set(self, data, async=False):
        new = [e for e in data if e['id'] is '+']
        list(map(self.request_new, new))
