from django.urls import path
from django.contrib import admin
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path("", views.index, name="index"),
    path("me", views.events_mine, name="events_mine"),
    path("event/<str:code>", views.events_main, name="event_view"),
]
