import requests
from bs4 import BeautifulSoup as beautifulsoup
import re
from core import Action


class Auth(object):
    def __init__(self, username, password):
        self.username = username
        self.password = password

    def do(self, conn):
        result = conn.get('classlogin?resource=%2Fsaa%2Fproducts%2Fwelcome')
        user = conn.translate.get_dict(result)['j_security_check']
        user['j_username'] = self.username
        user['j_password'] = self.password
        result = conn.post('j_security_check', data=user)
        login_links = result('script', text=re.compile('writeLoginURL.*();'))
        conn.signed_in = (len(login_links) == 0)
        if not conn.signed_in:
            raise Exception('%s: Invalid NOAA user or wrong password.'
                            % self.username)


class Translate(object):
    def get_value(self, e):
        return (dict([(o['value'], o.text)
                      for o in e.find_all('option', value=re.compile('.+'))])
                if e.name == 'select' else '')

    def get_field_dict(self, form_soup):
        return dict([(e.attrs['name'], self.get_value(e))
                    for e in form_soup.find_all(name=['input', 'select'])
                    if 'name' in e.attrs.keys()])

    def get_dict(self, html):
        forms = html.select('form')
        result = [(f.attrs['action'], self.get_field_dict(f))
                  for f in forms if 'action' in f.attrs]
        return dict(result)


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
        self.base_uri = 'https://www.nsof.class.noaa.gov/saa/products/'
        self.headers = {'User-Agent': 'Mozilla/5.0'}
        self.session = requests.Session()
        self.authenticate = Auth(username, password)
        self.get('welcome')
        self.translate = Translate()
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


def connect(username, password):
    return Connection(username, password)
