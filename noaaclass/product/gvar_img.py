from noaaclass import core
import re


class Subscriber(object):
    def row_to_dict(self, row):
        elements = row.select('td')
        _id = elements[3].a.text
        enabled = (elements[1].renderContents().strip() == 'Yes')
        result = (_id, {
            'enabled': enabled,
            'name': elements[2].a.text,
            'edit': (self.item_url % (_id, 'Y' if enabled else 'N'))
        })
        return result

    @property
    def list(self):
        rows = self.conn.get('subscriptions').select(
            'table.class_table tr:nth-of-type(2)')
        return dict([self.row_to_dict(r) for r in rows])


class api(core.api):
    def subscribe_get(self):
        data = (self.conn.get('subscriptions').select(
            '.class_table tr td:nth-of-type(4) a'))
        enabled = lambda x: re.match(r'.*%22(.*)%22.*', x).group(1) == 'Y'
        data = [{'id': d.text, 'enabled': enabled(d['href'])} for d in data]
        for d in data:
            page = self.conn.get('sub_details?sub_id=%s&enabled=%s'
                                 % (d['id'], 'Y' if d['enabled'] else 'N'))
            d['north'] = float(self.get_textbox(page, 'nlat'))
            d['south'] = float(self.get_textbox(page, 'slat'))
            d['west'] = float(self.get_textbox(page, 'wlon'))
            d['east'] = float(self.get_textbox(page, 'elon'))
            d['coverage'] = self.get_checkbox(page, 'Coverage')
            d['schedule'] = self.get_checkbox(page, 'Schedule')
            d['satellite'] = self.get_select(page, 'Satellite')
        return data

    def subscribe_new(self, e):
        name = __name__.split('.')[-1].upper()
        self.conn.get('sub_details?sub_id=0&'
                      'datatype_family=%s&submit.x=40&submit.y=11' %
                      name)
        data = {
            'df': name,
            'search_opt': 'SC',
            'gid_pattern': '',
            'orb_pattern': '',
            'sub_page_source': 'sub_search',
            'subhead_sub_enabled': 'Y' if e['enabled'] else 'N',
            'subhead_sub_description': ('[auto] %s %s' %
                                        (str(e['north']), str(e['west']))),
            'nlat': str(e['north']),
            'slat': str(e['south']),
            'wlon': str(e['west']),
            'elon': str(e['east']),
            'minDiff': '1.0',
            'Coverage': e['coverage'][0],
            'Satellite': e['satellite'][0],
            'Satellite Schedule': e['schedule'][0],
            'limit_search': 'Y',
            'max_lat_range': '180',
            'max_lon_range': '359',
        }
        self.conn.post('sub_deliver', data)
        channel_mask = list('000000' + 'X' * 24)
        for i in e['channel']:
            channel_mask[i-1] = '1'
        data = {
            'sub_page_source': 'sub_deliver',
            'sub_sched_opt': 'N',
            'sub_notif_opt': 'Y',
            'digital_sig_opt': 'N',
            'headers_opt': 'Y',
            'deliv_manifest_tda': '0',
            'deliv_checksum_opt': 'N',
            'geo_%s' % name: 'Y',
            'bits_%s' % name: '16',
            'format_%s' % name: e['format'],
            'channels_%s' % name: ''.join(channel_mask),
            'chan_%s' % name: str(e['channel'][0]),
            'visresolution': '1',
            'irresolution': '1',
            'spat_%s' % name: '1,1',
            'map_%s' % name: 'Y'
        }
        return self.conn.post('sub_save', data)

    def subscribe_edit(self, e):
        pass

    def subscribe_remove(self, e):
        pass

    def subscribe_set(self, data):
        old_data = self.request_get()
        remove = [e for e in old_data
                  if e['id'] not in [x['id'] for x in data]]
        new = [e for e in data if e['id'] is '+']
        edit = [e for e in data if e not in new and '+' in e['id']]
        [self.subscribe_new(e) for e in new]
        [self.subscribe_edit(e) for e in edit]
        [self.subscribe_remove(e) for e in remove]
        return self.request_get()

    def request_get(self):
        return {}

    def request_set(self, data):
        return {}
