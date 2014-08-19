import requests
from bs4 import BeautifulSoup as beautifulsoup
import re
from core import Action
import itertools


class Auth(object):
    def __init__(self, username, password):
        self.username = username
        self.password = password

    def do(self, conn):
        result = conn.get('classlogin?resource=%2Fsaa%2Fproducts%2Fwelcome',
                          'https')
        user = conn.translator.get_forms(result)['frmLogin']
        user['j_username'] = self.username
        user['j_password'] = self.password
        result = conn.post('j_security_check', data=user, proto='https',
                           form_name='frmLogin')
        login_links = result('script', text=re.compile('writeLoginURL.*();'))
        conn.signed_in = (len(login_links) == 0)
        if not conn.signed_in:
            raise Exception('%s: Invalid NOAA user or wrong password.'
                            % self.username)


class Translator(object):
    def get_value(self, elements, show_value):
        for e in elements:
            if 'name' in e.attrs.keys():
                yield (e.attrs['name'],
                       getattr(self, 'get_%s_value' % e.name)(e, show_value))

    def get_input_value(self, e, show_value):
        value = ''
        is_single = (lambda x: 'type' not in e.attrs
                     or e.attrs['type'] in ['text', 'hidden'])
        is_checked = (lambda x: 'checked' in e.attrs
                      and e.attrs['checked'] in ['1', 'Y'])
        all_values = not show_value
        if 'value' in e.attrs:
            if (is_single(e) or is_checked(e) or all_values):
                value = e.attrs['value']
        return value

    def get_select_value(self, e, show_value):
        values = e.select('option%s' % ('[selected]' if show_value else ''))
        values = [o.attrs['value'] for o in values if o.attrs['value']]
        return values

    def tuple_to_dict(self, list_of_tuples):
        _aux = dict((k, [v[1] for v in vs])
                    for (k, vs) in
                    itertools.groupby(list_of_tuples, lambda x: x[0]))
        cleaned = lambda l: [e for e in l if e != '']
        clear = lambda l: cleaned(l) if len(cleaned(l)) else ['']
        resume = lambda (k, v): (k, clear(v if not isinstance(v[0], list)
                                          else v[0]))
        return dict(map(resume, _aux.items()))

    def get_fields(self, form_soup, show_value):
        elements = [e for e in self.get_value(
            form_soup.find_all(name=['input', 'select']), show_value)]
        result = self.tuple_to_dict(elements)
        return result

    def get_forms(self, html, list_options=False):
        forms = html.select('form')
        result = [(f.attrs['name'], self.get_fields(f, not list_options))
                  for f in forms if 'name' in f.attrs]
        return dict(result)

    def simplify(self, element):
        return ('' if not len(element) else
                element[0:len(element)])

    def plain(self, form):
        for k, v in form.items():
            if isinstance(v, list):
                for x in v:
                    yield (k, x)
            else:
                yield (k, v)

    def fill_form(self, page, name, data):
        forms = self.get_forms(page)
        clear = lambda x: x is not ''
        form = {k: filter(clear, v) for k, v in
                (forms[name]).items()}
        form = {k: data[k] if k in data.keys()
                else self.simplify(v)
                for k, v in form.items()}
        return [x for x in self.plain(form)]


class Request(Action):
    def get_main_form(self):
        html = self.conn.get('welcome')
        return html, 'search'


class Subscribe(Action):
    def get_main_form(self):
        html = self.conn.get('subscriptions')
        return html, 'sub_details'


class Connection(object):
    def __init__(self, username, password):
        self.base_uri = '://www.nsof.class.noaa.gov/saa/products/'
        self.headers = {'User-Agent': 'Mozilla/5.0'}
        self.session = requests.Session()
        self.authenticate = Auth(username, password)
        self.get('welcome')
        self.translator = Translator()
        self.authenticate.do(self)
        self.request = Request(self)
        self.subscribe = Subscribe(self)

    @property
    def cookies(self):
        self._cookies = requests.utils.cookiejar_from_dict(
            requests.utils.dict_from_cookiejar(self.session.cookies))
        return self._cookies

    @property
    def last_response(self):
        return self._last_response

    @last_response.setter
    def last_response(self, response):
        if response.status_code != requests.codes.ok:
            raise Exception('Connection error (%i).' % response.status_code)
        self._last_response = response

    @property
    def last_response_soup(self):
        return beautifulsoup(self.last_response.text)

    def get(self, url, proto='http'):
        self.last_response = self.session.get(proto + self.base_uri + url,
                                              headers=self.headers,
                                              cookies=self.cookies,
                                              allow_redirects=True,
                                              timeout=2)
        return self.last_response_soup

    def post(self, url, data, proto='http', form_name=None):
        form = self.translator.fill_form(self.last_response_soup,
                                         form_name if form_name else url, data)
        self.last_response = self.session.post(proto + self.base_uri + url,
                                               headers=self.headers,
                                               cookies=self.cookies,
                                               data=form,
                                               allow_redirects=True,
                                               timeout=2)
        return self.last_response_soup


def connect(username, password):
    return Connection(username, password)
