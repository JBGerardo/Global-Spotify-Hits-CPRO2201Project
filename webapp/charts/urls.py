from django.urls import path
from . import views

urlpatterns = [
    path(
        "top-songs/",
        views.top_songs_by_countries,
        name="top_songs_by_countries",
    ),
    path(
        "country-diversity/",
        views.country_diversity,
        name="country_diversity",
    ),
    path(
        "browser/",
        views.chart_browser,
        name="chart_browser",
    ),
]
