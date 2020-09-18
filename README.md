# OneEvent
A Django App to manage registration to events.

[![Pypi Version](https://img.shields.io/pypi/v/django-oneevent.svg)](https://pypi.org/project/django-oneevent/)
[![Python Versions](https://img.shields.io/pypi/pyversions/django-oneevent.svg)](https://pypi.org/project/django-oneevent/)
[![Build Status](https://travis-ci.com/gchazot/OneEvent.svg?branch=master)](https://travis-ci.com/gchazot/OneEvent)

## Usage

### Basics
The objective of OneEvent is to simplify provide people organising an event with a tool to:
* Let participants quickly self-register to the event
* Let participants update or cancel their registration to the event
* Ask participants simple questions about their registration. These are called "Choices", and the
possible answers are called "options".
* Provide aggregated views of participants and their choices to the organisers.

So, there are 2 categories of users for the app: **organisers** and **participants**.

#### Event creation (Organiser)
The story starts then when a user creates a new event. They then become the "organiser" of that
event. The creation process happens by filling in a few details about the event, like a title,
description and time frame. The organiser can also add some choices that participants will have to
make and the options that they will be able to choose.

Once the event is created, the organiser can **publish** the event to make it visible to other
users. They can then *invite* participants by sharing with them the registration URL to the event.

#### Registration (Participant)
When a user navigates to the registration page, they are provided with a single-page with all the
public details about the event (Location, date and time, description, etc.).

There, they can confirm or decline their attendance to the event and select their answer for each
of the choices that the organiser has asked them to make.

This is all that participants usually have to do.

#### Event management (Organiser)
Up until the event actually happens (the app is not very useful after that). Organisers can access
the event management page. There, they are provided with details of all the participants and their
choices, in tabular and aggregated views.

There they can also export that data to a spreadsheet format, to automate printing of customised
seat tags for example or any other exciting thing planned for the participants.

#### Event modification (Organiser)
At any point, the organiser can update the details of the event. Especially, there is a point at
which they will want to close registration to the event, or even archive it (hopefully after it's
happened).

**Special care** should be taken when modifying the choices and options provided to participants,
as those changes cannot be undone, and may result in loosing the choices that participants have
already made and saved.

### Advanced concepts
OneEvent provides a few advanced features to help with the organisation of complex events.

#### Multiple Organisers
It is possible to add more organisers to an event. They will get access to some of the management
features of the app so they can help with the organisation.

#### Registration limits
Organisers can define some limits for registration, all of them are optional:
* Maximum Number of Participants: Once the number of attending participants reaches that limits,
users that have not confirmed their attendance yet will be presented with an error message. Note
that a value of 0 (zero) means that there is no limit.
* Booking Close Time: If defined, users that have not confirmed attendance yet will not be allowed
to do it any more after this time.
* Choices close time: If defined, participants will still be able to modify their choices up until
this time. This time needs to be equal or later than the Booking Close Time.

#### Sessions
Some events require participants to choose which session they want to attend.

For example, I might be organising a small training of 30 mins in my company, in a room that can
take 10 people but I have to train 50 of them. This would be an ideal scenario to describe by
offering (at least) 5 different sessions that participants can choose from.

(Note that this can only be configured after the event has been created)

#### Pricing Categories
Sadly, sometimes, participants have to contribute to be able to attend your event. OneEvent provides
an easy way to track who has paid what they owe.

Multiple categories of price can be defined and named to offer different prices. Users can be
matched to each category based on the **groups** they belong to. More on users and groups in next
section about user accounts.

### User accounts
OneEvent relies on Django user and group management. This means it's your site that needs to
implement user authentication.

For most functionality, only **User** accounts are required to use the app. However, in order to
define multiple *Pricing Categories*, Users must be assigned into groups that allow OneEvent to
decide which category the user belongs to.

Making sure that users are in the Groups they are supposed to can be tricky, but this functionality
can prove particularly useful in corporate environments if your site's authentication system can
assign users to groups depending on the structure of your organisation.

## Installation
OneEvent is only tested with Django 1.11 running on Python 2.7. The instructions below assume those
are used. Feel free to report any successful experience using it with different versions. 

Note: As an example, have a look at the [`dev_server.sh`](dev_server.sh) file and the resulting
development site it creates. You may also have a look at
[this sandbox website](https://oneevent-sandbox.herokuapp.com/) and
[the repository that manages it](https://github.com/gchazot/oneevent-sandbox)

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

To benefit from the calendar invite function you must configure email sending.
* Start with the [corresponding section of Django docs](https://docs.djangoproject.com/en/3.0/topics/email/).
* Then also define the email address invite that emails will be coming from:
```python
ONEEVENT_CALENDAR_INVITE_FROM = "no-reply@my-domain.io"
```

A few customizations are available:
* Define the name of the site or the color of the navbar in settings.
```python
ONEEVENT_SITE_BRAND = "OneEvent Sandbox"
ONEEVENT_NAVBAR_COLOR = "green"
```
* Customise the authentication section in the navbar. To do this, just create in your site's
`<templates_folder>/oneevent/` folder one or more of the following template files and fill it with
your desired content:
  * `navbar_auth_avatar.html`: To customise just the user menu title
  * `navbar_auth_extra_actions.html`: To insert actions in the user menu
  * `navbar_auth.html`: To customise the entire user menu section

  A good starting point is to copy the file from our code.

## Development
The `dev_server.sh` script is here to help setting up a development site.

```shell script
./dev_server.sh run
```
This will start a local dev server running with its own virtualenv.

```shell script
./dev_server.sh test
```
This will run all the tests currently available in the codebase and provided by Django.

```shell script
./dev_server.sh --help
```
For more options the script has to offer.

## Releasing
#### Preparation
* Merge all desired changes to `master`
* Update `setup.cfg` with the new version number and commit
* Tag the desired version
* Push the tag to GitHub

#### Automatic release
[Travis the Builder](https://travis-ci.com/github/gchazot/OneEvent) takes care of everything.

#### Manual release process
A little more involved but it's Okay I guess
```shell script
rm -rf build/ dist/ django_oneevent.egg-info/
python setup.py sdist
twine upload dist/*
```
