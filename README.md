# OneEvent
A Django App to manage registration to events.

[![Build Status](https://travis-ci.org/gchazot/OneEvent.svg?branch=master)](https://travis-ci.org/gchazot/OneEvent)

## Installation
OneEvent is only tested with Django 1.11 running on Python 2.7. The instructions below assume those
are used. Feel free to report any successful experience using it with different versions. 

Note: As an example, have a look at the [`dev_server.sh`](dev_server.sh) file or the resulting
development site it creates.

#### Python package
First, install the python package:
```shell script
pip install django-oneevent
```
You will probably want to add it, potentially with a pinned down version, in your `requirements.txt`
or other dependency configuration you're using.

#### Django settings
Then you can add the app and its dependencies to your Django settings file:
```python
# settings.py

INSTALLED_APPS = [
    ...
    'oneevent',
    'crispy_forms',
    ...
]
```

OneEvent also uses a custom context processor to allow customising its navbar. This can be
configured by adding `'oneevent.context_processors.customise_navbar'` to the list of
`context_processors` in your `TEMPLATES` setting. As an example, here is how it's done for the
development site:
```python
TEMPLATES[0]['OPTIONS']['context_processors'].append('oneevent.context_processors.customise_navbar')
```

Also, the app uses the nice `django-crispy-forms` helper with its `bootstrap3` template pack to
render nice forms with minimal effort. So you will have to specify the template pack;
```python
CRISPY_TEMPLATE_PACK = 'bootstrap3'
```
And also customise message tags to map Django's `ERROR` level to Bootstrap's `danger` style:
```python
from django.contrib import messages
MESSAGE_TAGS = {
    messages.ERROR: 'danger',
}
```

#### Django URLs
Load the configuration for the URL views.

```python
from django.conf.urls import include, url

urlpatterns += [
    ...
    url(r'^', include('oneevent.urls')),
    ...
]
```

## Release
Manual release process
```shell script
rm -rf build/ dist/ django_oneevent.egg-info/
python setup.py sdist
twine upload [--repository-url https://test.pypi.org/legacy/] dist/*
```