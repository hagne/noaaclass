from noaaclass import core

translate = {
    'area': {
        'north': 'nlat',
        'south': 'slat',
        'east': 'elon',
        'west': 'wlon'
    }

}

class Subscriber(object):
    def __init__(self, conn):
        self.conn = conn
        self.item_url = 'sub_details?sub_id=%s&enabled=%s'

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
    @property
    def subscribe(self):
        return Subscriber(self.connection)

    @property
    def order():
        return None
