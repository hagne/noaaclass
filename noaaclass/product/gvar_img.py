from noaaclass import core


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
        return {}

    def subscribe_new(self, e):
        name = self.action_name.upper()
        self.conn.get('sub_details?sub_id=0&'
                      'datatype_family=%s&submit.x=40&submit.y=11' %
                      name)
        self.conn.post('sub_deliver', {
            'df': name,
            'search_opt': 'SC',
            'sub_page_source': 'sub_search',
            'subhead_sub_enabled': 'Y',
            'subhead_sub_description': '[auto] noaaclass library',
            'limit_search': 'Y',
            'max_lat_range': 180,
            'max_lon_range': 359,
            'nlat': e['north'],
            'slat': e['south'],
            'wlon': e['west'],
            'elon': e['east'],
            'Coverage': e['coverage'][0],
            'Satellite Schedule': e['schedule'][0],
            'Satellite': e['satellite'][0]
        })
        channels = len(e['channel'])
        data = {
            'sub_page_source': 'sub_deliver',
            'sub_sched_opt': 'N',
            'sub_notif_opt': 'Y',
            'digital_sig_opt': 'N',
            'headers_opt': 'Y',
            'deliv_manifest_tda': 0,
            'deliv_checksum_opt': 'N',
            'geo_%s' % name: 'Y',
            'bits_%s' % name: 16,
            'format_%s' % name: e['format'],
            'channels_%s' % name: '1' * channels + 'X' * (29-channels),
            'chan_%s' % name: e['channel'][0],
            'visresolution': 1,
            'irresolution': 1,
            'spat_%s' % name: '1,1',
            'map_%s' % name: 'Y'
        }
        result = self.conn.post('sub_save', data)
        print result

    def subscribe_edit(self, e):
        pass

    def subscribe_remove(self, e):
        pass

    def subscribe_set(self, data):
        new = [e for e in data if e['id'] is '+']
        edit = [e for e in data if e not in new and '+' in e['id']]
        remove = [e for e in data if '+' not in e['id'] and '-' in e['id']]
        [self.subscribe_new(e) for e in new]
        [self.subscribe_edit(e) for e in edit]
        [self.subscribe_remove(e) for e in remove]
        return {}

    def request_get(self):
        return {}

    def request_set(self, data):
        return {}
