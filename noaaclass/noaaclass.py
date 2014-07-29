import requests
from bs4 import BeautifulSoup as beautifulsoup
from core import Command
import re


class SignIn(Command):
    def __init__(self, username, password):
        self.username = username
        self.password = password

    def do(self, conn):
        result = conn.get('classlogin?resource=%2Fsaa%2Fproducts%2Fwelcome')
        user = conn.parser.get_form_dict(result)['j_security_check']
        user['j_username'] = self.username
        user['j_password'] = self.password
        result = conn.post('j_security_check', data=user)
        login_links = result('script', text=re.compile('writeLoginURL.*();'))
        conn.signed_in = (len(login_links) == 0)
        if not conn.signed_in:
            raise Exception('%s: Invalid NOAA user or wrong password.'
                            % self.username)


class Parser(object):
    def get_value(self, e):
        return (dict([(o['value'], o.text)
                      for o in e.find_all('option', value=re.compile('.+'))])
                if e.name == 'select' else '')

    def get_field_dict(self, form_soup):
        return dict([(e.attrs['name'], self.get_value(e))
                    for e in form_soup.find_all(name=['input', 'select'])
                    if 'name' in e.attrs.keys()])

    def get_form_dict(self, html_soup):
        forms = html_soup.find_all('form')
        result = [(f.attrs['action'], self.get_field_dict(f))
                  for f in forms]
        return dict(result)


class Connection(object):
    def __init__(self, username, password):
        self.base_uri = 'https://www.nsof.class.noaa.gov/saa/products/'
        self.headers = {'User-Agent': 'Mozilla/5.0'}
        self.session = requests.Session()
        self.signin = SignIn(username, password)
        self.get('welcome')
        self.parser = Parser()
        self.signin.do(self)

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

    def get(self, url):
        self.last_response = self.session.get(self.base_uri + url,
                                              headers=self.headers,
                                              cookies=self.cookies)
        return beautifulsoup(self.last_response.text)

    def post(self, url, data):
        self.last_response = self.session.post(self.base_uri + url,
                                               headers=self.headers,
                                               cookies=self.cookies,
                                               data=data)
        return beautifulsoup(self.last_response.text)

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
        form = self.parser.get_form_dict(self.get('welcome'))['search']
        return [k.lower() for k in form['datatype_family'].keys()
                if self.has_local_api(k.lower())]


def connect(username, password):
    return Connection(username, password)
