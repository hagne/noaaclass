from noaaclass import core
import re
from datetime import datetime


class api(core.api):
    def register(self):
        self.name = 'GVAR_IMG'
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

    def subscribe_get(self):
        noaa = self.conn
        page = noaa.get('subscriptions')
        data = page.select('.class_table td a')
        enabled = lambda x: re.match(r'.*%22(.*)%22.*', x).group(1) == 'Y'
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
        return data

    def subscribe_new(self, e):
        name = __name__.split('.')[-1].upper()
        self.conn.get('sub_details?sub_id=0&'
                      'datatype_family=%s&submit.x=40&submit.y=11' %
                      name)
        data = self.local_to_post(e)
        self.conn.post('sub_deliver', data, form_name='sub_frm')
        channel_mask = list('000000' + 'X' * 24)
        data = self.local_to_post(e)
        for i in e['channel']:
            channel_mask[i-1] = '1'
            data['channels_%s' % name] = ''.join(channel_mask),
        self.conn.post('sub_save', data, form_name='sub_frm')

    def subscribe_edit(self, e):
        name = __name__.split('.')[-1].upper()
        data = self.local_to_post(e)
        self.conn.get('sub_details?sub_id=%s&enabled=%s'
                      % (e['id'], data['subhead_sub_enabled']))
        data = self.local_to_post(e)
        self.conn.post('sub_deliver', data, form_name='sub_frm')
        channel_mask = list('000000' + 'X' * 24)
        data = self.local_to_post(e)
        for i in e['channel']:
            channel_mask[i-1] = '1'
            data['channels_%s' % name] = ''.join(channel_mask),
        self.conn.post('sub_save', data, form_name='sub_frm')

    def subscribe_remove(self, e):
        self.conn.get('sub_delete?actionbox=%s' % e['id'])

    def subscribe_set(self, data):
        select = lambda i, data: [d for d in data if d['id'] == i][0]
        changed = lambda x, data: x != select(x['id'], data)
        old_data = self.subscribe_get()
        remove = [e for e in old_data
                  if e['id'] not in [x['id'] for x in data]]
        new = [e for e in data if e['id'] is '+']
        edit = [e for e in data if e not in new and changed(e, old_data)]
        list(map(lambda e: self.subscribe_new(e), new))
        list(map(lambda e: self.subscribe_edit(e), edit))
        list(map(lambda e: self.subscribe_remove(e), remove))

    def request_get(self):
        noaa = self.conn
        page = noaa.get('order_list')
        forms = noaa.translator.get_forms(noaa.last_response_soup)
        tmp = forms['o_form']
        tmp['hours'] = ['100']
        tmp['type'] = ['USER']
        tmp['submit'] = ['Submit']
        page = noaa.post('order_list', tmp, form_name='o_form')
        data = page.select('.zebra td a')
        data = [{'id': d.text}
                for d in data if d.text.isdigit()]
        url = [
            'order_details?order=%s&hours=&status_page=1&group_size=25',
            ('item_query?item=%s&order=%s&hours=&status_page=1&page=1'
             '&group_size=25')
            ]
        # import ipdb; ipdb.set_trace()
        for d in data:
            noaa.get(url[0] % d['id'])
            table = noaa.last_response_soup.select('.class_table td')
            d['delivered'] = (table[4].text is 'Order Delivered')
            d['datetime'] = datetime.strptime(table[3].text,
                                              '%Y-%m-%d %H:%M:%S')
            d['format'] = ''
            item = lambda i: i.text
            items = map(item, noaa.last_response_soup.select('.zebra td a'))
            d['files'] = []
            for i in items:
                noaa.get(url[1] % (i, d['id']))
                head = noaa.last_response_soup.select('.class_table td')
                area = [head[h].text for h in range(8, 12)]
                d['format'] = head[1].text
                coords = ['south', 'north', 'west', 'east']
                for c in range(len(coords)):
                    d[coords[c]] = float(area[c]) / 100
                item = lambda row, i: row.select('td')[i].text
                file_data = lambda row: (item(row, 3), int(item(row, 5)))
                files = map(file_data,
                            noaa.last_response_soup.select('.zebra tr')[1:])
                d['files'].extend(files)
        return data

    def request_set(self, data):
        return {}
