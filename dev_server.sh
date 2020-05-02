#!/bin/bash

function usage() {
  echo ""
  echo "Usage: $0 [options] action"
  echo "Available options:"
  echo "  -h|--help: Display this help message and exit"
  echo "  -d|--delete-existing: Delete existing folder without asking"
  echo "  -k|--keep-existing: Keep existing folder without asking"
  echo ""
  echo "Available actions:"
  echo "  start: Launch a local development server"
  echo "  test: Run tests and exit"
  echo ""
}

DELETE_EXISTING="ask"
ACTION=""

while (( "$#" )); do
  case "$1" in
    -d|--delete-existing)
      DELETE_EXISTING="yes"
      shift
      ;;
    -k|--keep-existing)
      DELETE_EXISTING="no"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    run|test)
      ACTION="$1"
      shift
      ;;
    -*|--*=) # unsupported flags
      echo "Error: Unsupported flag $1" >&2
      usage
      exit 1
      ;;
    *) # unsupported action
      echo "Error: Unsupported action $1" >&2
      usage
      exit 1
      ;;
  esac
done

BASE_REPO=$(dirname "$(readlink -f "$0")")
TARGET_DIR=${BASE_REPO}/dev_site

if [ -d "$TARGET_DIR" ]; then
  if [ ${DELETE_EXISTING} == "ask" ]; then
    echo "Target already exists: $TARGET_DIR"
    echo -n "Do you want to delete it ? [y/N]: "
    read answer
    if [ "y" == "$answer" ] ||  [ "Y" == "$answer" ]; then
        DELETE_EXISTING="yes"
    else
        exit 1;
    fi
  fi

  if [ ${DELETE_EXISTING} == "yes" ]; then
    rm -rf "$TARGET_DIR"
  fi
fi

PROJECT_DIR=${TARGET_DIR}/dev_project
VENV_DIR=${TARGET_DIR}/venv

mkdir -p "${PROJECT_DIR}"

if [ ! -f "${VENV_DIR}/bin/activate" ]; then
  virtualenv -p "$(command -v python2)" "${VENV_DIR}"
fi
source "${VENV_DIR}/bin/activate"

pip install -e "${BASE_REPO}[test]"

SITE_NAME=oneevent_site
SITE_DIR="${PROJECT_DIR}/${SITE_NAME}"
if  [ ! -d "${SITE_DIR}" ]; then
  django-admin startproject "${SITE_NAME}" "${PROJECT_DIR}"


  cat << EOF >> "${SITE_DIR}/settings.py"

INSTALLED_APPS += [
    'oneevent',
    'crispy_forms',
    'django_extensions',
    'debug_toolbar',
]

MIDDLEWARE += [
    'debug_toolbar.middleware.DebugToolbarMiddleware',
]

INTERNAL_IPS = [
    '127.0.0.1',
]

TEMPLATES[0]['OPTIONS']['context_processors'].append('oneevent.context_processors.customise_navbar')

# Override the "error" message level to match the bootstrap "danger" class
from django.contrib import messages
MESSAGE_TAGS = {
    messages.ERROR: 'danger',
}

# django-crispy-forms template pack
CRISPY_TEMPLATE_PACK = 'bootstrap3'

EOF

  cat << EOF >> "${SITE_DIR}/urls.py"

from django.conf import settings
from django.conf.urls import include, url
from django.contrib.auth import views as auth_views

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
         url(r'^__debug__/', include(debug_toolbar.urls)),
    ]

urlpatterns += [
    url(r'^accounts/login/$', auth_views.LoginView.as_view(), name='login'),
    url(r'^accounts/logout/$', auth_views.LogoutView.as_view(), name='logout'),
    url(r'^', include('oneevent.urls')),
]

EOF

fi

MANAGE_COMMAND="${PROJECT_DIR}/manage.py"

if [ "${ACTION}" == "test" ]; then
  "${MANAGE_COMMAND}" check || exit 11
  "${MANAGE_COMMAND}" makemigrations --dry-run --check || exit 12
  "${MANAGE_COMMAND}" test || exit 13
  exit 0
elif [ "${ACTION}" == "run" ]; then
  set -e
  "${MANAGE_COMMAND}" check
  "${MANAGE_COMMAND}" migrate
  "${MANAGE_COMMAND}" runserver "0.0.0.0:8000"
  exit 0
fi;

exit 2  # How did we get here?
