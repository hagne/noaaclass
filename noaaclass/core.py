class Action(object):
    def __init__(self, conn):
        self.conn = conn

    def load(self, lib):
        return __import__(lib, fromlist=[''])

    def __getattr__(self, name):
        try:
            return self.load('noaaclass.product.%s' % name).api(self)
        except Exception, e:
            raise Exception('There is no API to the "%s" product.\n%s'
                            % (name, e))

    def has_local_api(self, product):
        try:
            getattr(self, product)
        except Exception:
            return False
        return True

    def products(self):
        html, form_name = self.get_main_form()
        form = self.conn.translate.get_dict(html)[form_name]
        return [k.lower() for k in form['datatype_family'].keys()
                if self.has_local_api(k.lower())]


class api(object):
    def __init__(self, action):
        self.action = action

    @property
    def conn(self):
        return self.action.conn

    @property
    def action_name(self):
        return self.action.__class__.__name__.lower()

    def get_select(self, page, name):
        options = page.select('form select[name=%s] option' % name)
        return [o['value'] for o in options if 'selected' in o.attrs]

    def get_checkbox(self, page, name):
        return [i['value'] for i in page.select('form input[name~=%s]' % name)
                if 'checked' in i.attrs]

    def get_textbox(self, page, name):
        return page.select('form input[name~%s]' % name)[0].attrs['value']

    def get(self):
        return getattr(self, '%s_get' % self.action_name)()

    def set(self, data):
        return getattr(self, '%s_set' % self.action_name)(data)
