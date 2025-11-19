from django.urls import path

from . import views

urlpatterns = [
    path(
        "top-songs/",
        views.top_songs_by_countries,
        name="top_songs_by_countries",
    ),
]
