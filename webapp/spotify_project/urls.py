"""
- expose the Django admin under "/admin/"
- route the root URL ("/") to the charts landing page
- include all charts-related URLs under the "/charts/" prefix
"""

from django.contrib import admin
from django.urls import path, include

# Import the landing page view from the charts app
from charts import views as charts_views

urlpatterns = [
    # Django admin interface
    path("admin/", admin.site.urls),

    # Root URL → charts landing page
    path("", charts_views.landing_page, name="landing"),

    # All charts-related pages under /charts/
    path("charts/", include("charts.urls")),
]
