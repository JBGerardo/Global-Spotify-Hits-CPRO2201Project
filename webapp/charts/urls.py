"""
URL configuration for the charts app.

These URLs are included under the "/charts/" prefix in the project-level
urls.py file. Each path points to a simple function-based view in
charts/views.py.
"""

from django.urls import path
from . import views

urlpatterns = [
    # Landing page for the charts section
    path("", views.landing_page, name="landing"),

    # Top tracks by total streams (2023)
    path("top-streams/", views.top_streams, name="top_streams"),

    # Top songs by number of countries they appear in (2023)
    path("top-songs/", views.top_songs_by_countries, name="top_songs"),

    # Country chart diversity (unique tracks per country)
    path(
        "country-diversity/",
        views.country_diversity,
        name="country_diversity",
    ),

    # Raw browser with filters + pagination
    path("browser/", views.chart_browser, name="chart_browser"),
]
