#!/bin/bash

if [ $# -lt 1 ]; then
    echo "Usage: $0 <target_dir> [<branch>]"
    exit 1
fi

TARGET_DIR=$1
SOURCE_BRANCH=$2
if [ -z "$SOURCE_BRANCH" ]; then
    SOURCE_BRANCH="@local"
fi

ORIGIN_REPO=$(dirname $(readlink -f $0))

if [ -d $TARGET_DIR ]; then
    echo "Target already exists: $TARGET_DIR"
    echo -n "Do you want to delete it ? [y/N]: "
    read answer
    if [ "y" == "$answer" -o "Y" == "$answer" ]; then
        rm -rf $TARGET_DIR
    else
        exit 2
    fi
fi

mkdir -p $TARGET_DIR
cd $TARGET_DIR

virtualenv venv
source venv/bin/activate
pip install -r $ORIGIN_REPO/requirements.txt

django-admin startproject mysite
cd mysite

if [ $SOURCE_BRANCH == "@local" ]; then
    ln -s $ORIGIN_REPO oneevent
else
    git clone -b $SOURCE_BRANCH -- $ORIGIN_REPO oneevent
fi
# Create an initial DB (django_debug_toolbar requires it)
./manage.py migrate

cat << EOF >> mysite/settings.py

INSTALLED_APPS += ('oneevent',
    'crispy_forms',
    'django_extensions',
    'debug_toolbar',
)
TEMPLATES[0]['OPTIONS']['context_processors'].append('oneevent.context_processors.customise_navbar')

# Override the "error" message level to match the bootstrap "danger" class
from django.contrib import messages
MESSAGE_TAGS = {
    messages.ERROR: 'danger',
}

# django-crispy-forms template pack
CRISPY_TEMPLATE_PACK = 'bootstrap3'

EOF

cat << EOF >> mysite/urls.py

urlpatterns.extend([
    url(r'^accounts/login/$', 'django.contrib.auth.views.login', name='login'),
    url(r'^accounts/logout/$', 'django.contrib.auth.views.logout', name='logout'),
    url(r'^', include('oneevent.urls')),
])

EOF

./manage.py check
./manage.py test
./manage.py migrate

./manage.py runserver 0.0.0.0:8000
