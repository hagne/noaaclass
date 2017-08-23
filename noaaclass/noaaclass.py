#!/usr/bin/env python
# -*- coding: utf-8 -*-
import itertools
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from multiprocessing import cpu_count

import requests
import urllib3
from bs4 import BeautifulSoup as beautifulsoup
from requests.exceptions import ConnectionError

from .core import Action

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class Auth(object):
    def __init__(self, username, password):
        self.username = username
        self.password = password

    def load_home_page(self, conn):
        try:
            conn.get('classlogin?resource=%2Fsaa%2Fproducts%2Fwelcome',
                     'https')
        except ConnectionError:
            raise Exception('NOAA CLASS is down until %s.' %
                            str(conn.next_up_datetime()))

    def fill_login_form(self, conn):
        user = conn.translator.get_forms(conn.last_response_soup)['frmLogin']
        user['j_username'] = self.username
        user['j_password'] = self.password
        conn.post('j_security_check', data=user, proto='https',
                  form_name='frmLogin')

    def check_login_result(self, conn):
        page = conn.last_response_soup
        login_links = page('script', text=re.compile('writeLoginURL.*();'))
        conn.signed_in = (len(login_links) == 0)
        if not conn.signed_in:
            raise Exception('%s: Invalid NOAA user or wrong password.'
                            % self.username)

    def do(self, conn):
        seconds = self.load_home_page(conn)
        self.fill_login_form(conn)
        self.check_login_result(conn)
        return seconds


class Translator(object):
    def get_value(self, elements, show_value):
        for e in elements:
            if 'name' in e.attrs:
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
        resume = lambda k_v: (k_v[0], clear(k_v[1] if not isinstance(k_v[1][0], list)
                                            else k_v[1][0]))
        return dict(list(map(resume, list(_aux.items()))))

    def get_fields(self, form_soup, show_value):
        parse = lambda frm, cls: [e for e in self.get_value(
                frm.select(cls), show_value
        )]
        elements = parse(form_soup, 'input')
        elements.extend(parse(form_soup, 'select'))
        result = self.tuple_to_dict(elements)
        return result

    def get_forms(self, html, list_options=False):
        forms = html.select('form')
        scrap_form = lambda f: (f.attrs['name'],
                                self.get_fields(f, not list_options))
        has_name = lambda f: 'name' in f.attrs
        result = list(map(scrap_form, list(filter(has_name, forms))))
        return dict(result)

    def simplify(self, element):
        return ('' if not len(element) else
                element[0:len(element)])

    def plain(self, form):
        for k, v in list(form.items()):
            if isinstance(v, list):
                for x in v:
                    yield (k, x)
            else:
                yield (k, v)

    def fill_form(self, page, name, data):
        forms = self.get_forms(page)
        clear = lambda x: x is not ''
        form = {k: list(filter(clear, v)) for k, v in
                list((forms[name]).items())}
        form = {k: data[k] if k in list(data.keys())
        else self.simplify(v)
                for k, v in list(form.items())}
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
    def __init__(self, username=None, password=None, verify=False):
        self.headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.125 YaBrowser/17.7.1.716 (beta) Yowser/2.5 Safari/537.36'}
        self.session = requests.Session()
        self.verify = verify
        if username and password:
            self.base_uri = '://www.class.ncdc.noaa.gov/saa/products/'
            self.authenticate = Auth(username, password)
            self.get('welcome')
            self.translator = Translator()
            self.authenticate.do(self)
            self.request = Request(self)
            self.subscribe = Subscribe(self)
        else:
            self.base_uri = '://www.class.ncdc.noaa.gov/saa/products/'

    def next_up_datetime(self):
        end = datetime.utcnow()
        self.get('')
        middle = self.last_response_soup.select('#middle p')
        if len(middle) > 0:
            text = middle[1].text
            regex = re.compile(", (.*), from (.*) UTC .* through (.*) UTC")
            params = list(regex.findall(text)[0])
            pattern = '%m/%d/%y %H%M'
            begin = datetime.strptime('%s %s' % tuple(params[0:2]), pattern)
            end = datetime.strptime('%s %s' % (params[0], params[2]), pattern)
            if begin >= end:
                end += timedelta(days=1)
        from pytz import utc
        return end.replace(tzinfo=utc)

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
        packed = self.pack(response).select('h1')
        if (response.status_code != requests.codes.ok or
                (packed and 'An Error Occurred' in packed[0].text)):
            raise Exception('Connection error (%i).' % response.status_code)
        self._last_response = response

    @property
    def last_response_soup(self):
        return self.pack(self.last_response)

    def get(self, url, proto='https'):
        """
        Load an url using the GET method.

        Keyword arguments:
        url -- the Universal Resource Location
        proto -- the protocol (default 'http')
        """
        self.last_response = self.session.get(proto + self.base_uri + url,
                                              headers=self.headers,
                                              cookies=self.cookies,
                                              allow_redirects=True,
                                              verify=self.verify)
        return self.last_response_soup

    def pack(self, response, async=False):
        soup = beautifulsoup(response.text, "lxml")
        if async:
            response.close()
        return soup

    def getmultipleasync(self, urls, proto='https'):
        reqs = [[[proto + self.base_uri + u],
                 {
                     "headers"        : self.headers,
                     # "session": self.session,
                     "cookies"        : self.cookies,
                     "allow_redirects": True
                 }] for u in urls]
        with ThreadPoolExecutor(max_workers=cpu_count()) as pool:
            result = pool.map(lambda p: requests.get(*p[0], **p[1]), reqs)
        return result

    def getmultiplesync(self, urls, proto='https'):
        result = []
        for u in urls:
            self.get(u, proto)
            result.append(self.last_response)
        return result

    def getmultiple(self, urls, proto='https', async=False):
        result = []
        if len(urls) > 0:
            fx = self.getmultipleasync if async else self.getmultiplesync
            result = fx(urls, proto)
            result = [x for x in result if x is not None]
        return list(map(lambda r, a=async: self.pack(r, a), result))

    def post(self, url, data, proto='https', form_name=None):
        """
        Load an url using the POST method.

        Keyword arguments:
        url -- the Universal Resource Location
        data -- the form to be sent
        proto -- the protocol (default 'http')
        form_name -- the form name to search the default values
        """
        form = self.translator.fill_form(self.last_response_soup,
                                         form_name if form_name else url, data)
        self.last_response = self.session.post(proto + self.base_uri + url,
                                               headers=self.headers,
                                               cookies=self.cookies,
                                               data=form,
                                               allow_redirects=True,
                                               verify=self.verify)
        return self.last_response_soup


def connect(username, password):
    return Connection(username, password)


def next_up_datetime():
    conn = Connection()
    return conn.next_up_datetime()
