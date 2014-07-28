import requests
from bs4 import BeautifulSoup as beautifulsoup


class Command(object):
    def do(self, conn):
        raise Exception('Subclass responsability!')


class SignIn(Command):
    def __init__(self, username, password):
        self.username = username
        self.password = password

    def do(self, conn):
        conn.get('classlogin?resource=%2Fsaa%2Fproducts%2Fwelcome')
        user = {
            'j_username': self.username,
            'j_password': self.password
        }
        result = conn.post('j_security_check', data=user)
        import re
        login_links = result('script', text=re.compile('writeLoginURL.*();'))
        conn.signed_in = (len(login_links) == 0)
        if not conn.signed_in:
            raise Exception('%s: Invalid NOAA user or wrong password.'
                            % self.username)


class Connection(object):
    def __init__(self, username, password):
        self.base_uri = 'https://www.nsof.class.noaa.gov/saa/products/'
        self.headers = {'User-Agent': 'Mozilla/5.0'}
        self.session = requests.Session()
        self.signin = SignIn(username, password)
        self.get('welcome')
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
            return self.load('noaaclass.product.%s' % name)
        except Exception:
            raise Exception('There is no API to the "%s" product.' % name)


def connect(username, password):
    return Connection(username, password)
