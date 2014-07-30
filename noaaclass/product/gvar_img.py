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

    def subscribe_set(self, data):
        return {}

    def request_get(self):
        return {}

    def request_set(self, data):
        return {}
