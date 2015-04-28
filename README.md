noaaclass
=========

[![Gitter](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/gersolar/noaaclass?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

[![License](https://img.shields.io/pypi/l/noaaclass.svg)](https://raw.githubusercontent.com/gersolar/noaaclass/master/LICENSE) [![Downloads](https://img.shields.io/pypi/dm/noaaclass.svg)](https://pypi.python.org/pypi/noaaclass/) [![Build Status](https://travis-ci.org/gersolar/noaaclass.svg?branch=master)](https://travis-ci.org/gersolar/noaaclass) [![Coverage Status](https://coveralls.io/repos/gersolar/noaaclass/badge.png)](https://coveralls.io/r/gersolar/noaaclass) [![Code Health](https://landscape.io/github/gersolar/noaaclass/master/landscape.png)](https://landscape.io/github/gersolar/noaaclass/master) [![PyPI version](https://badge.fury.io/py/noaaclass.svg)](http://badge.fury.io/py/noaaclass)
[![Stories in Ready](https://badge.waffle.io/gersolar/noaaclass.png?label=ready&title=Ready)](https://waffle.io/gersolar/noaaclass)

A python library that allow to request images to the NOAA CLASS (Comprehensive Large Array-Data Stewardship System).


Requirements
------------

If you want to use this library on any GNU/Linux or OSX system you just need to execute:

    $ pip install noaaclass

If you want to improve this library, you should download the [github repository](https://github.com/gersolar/noaaclass) and execute:

    $ make deploy


Testing
-------

To test all the project you should use the command:

    $ make test

If you want to help us or report an issue join to us through the [GitHub issue tracker](https://github.com/gersolar/noaaclass/issues).


Example
--------

It can show all the supported products to be subscribed:

```python
from noaaclass import noaaclass
noaa = noaaclass.connect('username', 'password')
print noaa.subscribe.products()
```

Then it can *create new* **subscriptions** to the **gvar_img** product:

```python
from noaaclass import noaaclass
noaa = noaaclass.connect('username', 'password')
data = [
    {
        'id': '+',
        'enabled': True,
        'name': '[auto] sample1',
        'north': -26.72,
        'south': -43.59,
        'west': -71.02,
        'east': -48.52,
        'coverage': ['SH'],
        'schedule': ['R'],
        'satellite': ['G13'],
        'channel': [1],
        'format': 'NetCDF',
    },
    {
        'id': '+',
        'enabled': False,
        'name': '[auto] sample2',
        'north': -26.73,
        'south': -43.52,
        'west': -71.06,
        'east': -48.51,
        'coverage': ['SH'],
        'schedule': ['R'],
        'satellite': ['G13'],
        'channel': [2],
        'format': 'NetCDF',
    },
]
noaa.subscribe.gvar_img.set(data)
```

Next, you can *retrieve all* the subscriptions to the gvar_img product: 

```python
from noaaclass import noaaclass
noaa = noaaclass.connect('username', 'password')
data = noaa.subscribe.gvar_img.get()
```

Also, you can *modify* or *delete* the previous subscriptions:

```python
from noaaclass import noaaclass
noaa = noaaclass.connect('username', 'password')
data = noaa.subscribe.gvar_img.get()
data[1]['name'] = '[auto] name changed!'
data[1]['enabled'] = True
data.pop(0)
data = noaa.subscribe.gvar_img.set(data)
```

In the other hand, if you want an historic data raise a **request**:

```python
data = [
    {
        'id': '+',
        'north': -26.72,
        'south': -43.59,
        'west': -71.02,
        'east': -48.52,
        'coverage': ['SH'],
        'schedule': ['R'],
        'satellite': ['G13'],
        'channel': [1],
        'format': 'NetCDF',
        'start': datetime(2014, 9, 16, 10, 0, 0),
        'end': datetime(2014, 9, 16, 17, 59, 59)
    },
    {
        'id': '+',
        'north': -26.73,
        'south': -43.52,
        'west': -71.06,
        'east': -48.51,
        'coverage': ['SH'],
        'schedule': ['R'],
        'satellite': ['G13'],
        'channel': [2],
        'format': 'NetCDF',
        'start': datetime(2014, 9, 2, 10, 0, 0),
        'end': datetime(2014, 9, 3, 17, 59, 59)
    },
]
from noaaclass import noaaclass
noaa = noaaclass.connect('username', 'password')
data = noaa.request.gvar_img.set(data, async=True)
```

And, if you want to retrieve the requests made in the last 2 hours:

```python
from noaaclass import noaaclass
noaa = noaaclass.connect('username', 'password')
data = noaa.request.gvar_img.get(async=True, hours = 2, append_files=True)
```

Last, when the site is down you can get the next datetime (in UTC format) in which the website is going to be running:

```python
from noaaclass import noaaclass
noaaclass.next_up_datetime()
```


About
-----

This software is developed by [GERSolar](http://www.gersol.unlu.edu.ar/). You can contact us to [gersolar.dev@gmail.com](mailto:gersolar.dev@gmail.com).
