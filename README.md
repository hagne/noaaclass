noaaclass
=========

[![Build Status](https://travis-ci.org/ecolell/noaaclass.svg?branch=master)](https://travis-ci.org/ecolell/noaaclass) [![Coverage Status](https://coveralls.io/repos/ecolell/noaaclass/badge.png)](https://coveralls.io/r/ecolell/noaaclass) [![Code Health](https://landscape.io/github/ecolell/noaaclass/master/landscape.png)](https://landscape.io/github/ecolell/noaaclass/master)


A python library that allow to request images to the NOAA CLASS (Comprehensive Large Array-Data Stewardship System).


Requirements
------------

If you want to use this library on any GNU/Linux or OSX system you just need to execute:

    $ pip install noaaclass

If you want to improve this library, you should download the [github repository](https://github.com/ecolell/noaaclass) and execute:

    $ make deploy


Testing
-------

To test all the project you should use the command:

    $ make test

If you want to help us or report an issue join to us through the [GitHub issue tracker](https://github.com/ecolell/noaaclass/issues).


Example
--------

It can show all the supported products to be subscripted:

```python
import noaaclass
noaa = noaaclass.connect('username', 'password')
print self.noaa.subscribe.products()
```

Then it can create new **subscriptions** to the **gvar_img** product:

```python
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
self.noaa.subscribe.gvar_img.set(data)
```

Also, you can retrieve subscription from the noaa class subscripted:

```python
data = self.noaa.subscribe.gvar_img.get()
```

Last, you can modify or delete the previous subscriptions:

```python
data[1]['name'] = '[auto] name changed!'
data.pop(0)
data = self.noaa.subscribe.gvar_img.set(data)
```

About
-----

This software is developed by [GERSolar](http://www.gersol.unlu.edu.ar/). You can contact us to [gersolar.dev@gmail.com](mailto:gersolar.dev@gmail.com).
