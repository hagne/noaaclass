from noaaclass import core
import re
from datetime import datetime, timedelta

MAX_HOURS = '48'

select = lambda i, n, data: [d for d in data if d['id'] == i or d['name'] == n]
changed = lambda x, data: x != select(x['id'], x['name'], data)[0]
is_new = lambda e, old_data: (e['id'] is '+'
                              and not select(e['id'], e['name'], old_data))
is_removed = lambda e, data: e['id'] not in [x['id'] for x in data]
need_id = lambda e, old_data: not e['id'].isdigit() and not is_new(e, old_data)
enabled = lambda x: re.match(r'.*%22(.*)%22.*', x).group(1) == 'Y'
file_item = lambda row, i: row.select('td')[i].text
file_data = lambda row: (file_item(row, 3), int(file_item(row, 5)),
                         file_item(row, 4) == 'GVAR_IMG')


class api(core.api):
    def initialize(self):
        self.name = 'GVAR_IMG'
        self.name_upper = self.name.upper()
        direct = lambda x: x
        enabled_to_local = lambda x: x == 'Y'
        enabled_to_remote = lambda x: 'Y' if x else 'N'
        single = lambda x, t: t(x[0])
        multiple = lambda l, t: list(map(t, l))
        self.translate(single, 'enabled', enabled_to_local,
                       'subhead_sub_enabled', enabled_to_remote)
        self.translate(single, 'name', direct, 'subhead_sub_description', str)
        self.translate(single, 'north', float, 'nlat', str)
        self.translate(single, 'south', float, 'slat', str)
        self.translate(single, 'west', float, 'wlon', str)
        self.translate(single, 'east', float, 'elon', str)
        self.translate(multiple, 'coverage', direct, 'Coverage', direct)
        self.translate(multiple, 'schedule', direct, 'Satellite Schedule',
                       direct)
        self.translate(multiple, 'satellite', direct, 'Satellite', direct)
        self.translate(multiple, 'channel', int, 'chan_%s' % self.name, str)
        self.translate(single, 'format', direct, 'format_%s' % self.name, str)

    def subscribe_get_append_orders(self, noaa, d):
        noaa.get('order_list?order=%s&type=SUBS&displayDetails=Y&hours=%s'
                 '&status_page=1&group_size=25' % (d['id'], MAX_HOURS))
        item = lambda i: {'id': str(i.text)}
        is_item = lambda i: i.text.isdigit()
        d['orders'] = self.obtain_items(noaa, item, is_item)
        self.parse_orders(noaa, d['orders'])

    def subscribe_get(self, append_orders=False):
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
            join = lambda x, y: dict(x.items() + y.items())
            tmp = join(tmp, forms['sub_frm'])
            d.update(self.post_to_local(tmp))
            if append_orders:
                self.subscribe_get_append_orders(noaa, d)
        return data

    def subscribe_new(self, e):
        self.conn.get('sub_details?sub_id=0&'
                      'datatype_family=%s&submit.x=40&submit.y=11' %
                      self.name_upper)
        data = self.local_to_post(e)
        self.conn.post('sub_deliver', data, form_name='sub_frm')
        channel_mask = list('000000' + 'X' * 24)
        data = self.local_to_post(e)
        for i in e['channel']:
            channel_mask[i-1] = '1'
            data['channels_%s' % self.name_upper] = ''.join(channel_mask),
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
            channel_mask[i-1] = '1'
            data['channels_%s' % self.name_upper] = ''.join(channel_mask),
        self.conn.post('sub_save', data, form_name='sub_frm')

    def subscribe_remove(self, e):
        self.conn.get('sub_delete?actionbox=%s' % e['id'])

    def subscribe_classify(self, data):
        old_data = self.subscribe_get(append_orders=False)
        incomplete = [d for d in data if need_id(d, old_data)]
        for d in incomplete:
            d['id'] = select(d['id'], d['name'], old_data)[0]['id']
        remove = [e for e in old_data if is_removed(e, data)]
        new = [e for e in data if is_new(e, old_data)]
        edit = [e for e in data if e not in new and changed(e, old_data)]
        return remove, new, edit

    def subscribe_set(self, data, append_orders=False):
        remove, new, edit = self.subscribe_classify(data)
        list(map(self.subscribe_new, new))
        list(map(self.subscribe_edit, edit))
        list(map(self.subscribe_remove, remove))

    def parse_area(self, head, order):
        coords = ['south', 'north', 'west', 'east']
        for index in range(len(coords)):
            order[coords[index]] = float(head[8+index].text) / 100

    def parse_files(self, noaa, order):
        head = noaa.last_response_soup.select('.class_table td')
        order['format'] = head[1].text
        self.parse_area(head, order)
        files = map(file_data,
                    noaa.last_response_soup.select('.zebra tr')[1:])
        files = map(lambda x: (x[0], x[1]), filter(lambda x: x[2], files))
        order['files'].extend(files)

    def obtain_items(self, noaa, item_functor, check_functor):
        anchors = noaa.last_response_soup.select('.zebra td a')
        return map(item_functor, filter(check_functor, anchors))

    def parse_order(self, noaa, order):
        table = noaa.last_response_soup.select('.class_table td')
        order['delivered'] = (table[4].text
                              in ['Order Delivered', 'Order Ready'])
        order['datetime'] = datetime.strptime(table[3].text,
                                              '%Y-%m-%d %H:%M:%S')
        order['files'] = {'http': [], 'ftp': []}
        day_before_yesterday = datetime.utcnow() - timedelta(days=2)
        order['old'] = order['datetime'] < day_before_yesterday
        item = lambda i: i['href'].split("'")[1]
        is_http = lambda i: 'www' in i.text
        is_ftp = lambda i: 'ftp' in i.text
        for i in self.obtain_items(noaa, item, is_http):
            order['files']['http'].append(i)
        for i in self.obtain_items(noaa, item, is_ftp):
            order['files']['ftp'].append(i)

    def parse_orders(self, noaa, orders):
        for order in orders:
            noaa.get('order_details?order=%s&hours=%s&status_page=1'
                     '&group_size=25' % (order['id'], MAX_HOURS))
            self.parse_order(noaa, order)

    def request_get(self):
        noaa = self.conn
        page = noaa.get('order_list')
        forms = noaa.translator.get_forms(noaa.last_response_soup)
        tmp = forms['o_form']
        tmp['hours'] = [MAX_HOURS]
        tmp['type'] = ['USER']
        tmp['submit'] = ['Submit']
        page = noaa.post('order_list', tmp, form_name='o_form')
        data = page.select('.zebra td a')
        data = [{'id': d.text}
                for d in data if d.text.isdigit()]
        self.parse_orders(noaa, data)
        key = lambda x: x['start']
        data.sort(key=key)
        return data

    def request_set(self, data):
        return {}
