from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http.response import Http404

from .models import Event


def index(request):
    if request.user.is_authenticated:
        return redirect("events_mine")
    else:
        return render(request, "dds_registration/landing.html.django")


@login_required
def events_mine(request):
    if not request.user.is_authenticated:
        return redirect("index")

    return render(request, "dds_registration/mine.html.django")


def events_main(request, code):
    try:
        event = Event.objects.get(code=code)
    except Event.DoesNotExist:
        return Http404

    return render(request, "dds_registration/mine.html.django", {"event": event})
