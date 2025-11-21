from django.urls import path
from . import views

urlpatterns = [
    # Landing page for charts
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
