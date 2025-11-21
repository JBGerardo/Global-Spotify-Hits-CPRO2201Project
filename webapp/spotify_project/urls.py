from django.contrib import admin
from django.urls import path, include

# Use views from the charts app for the landing page
from charts import views as charts_views

urlpatterns = [
    # Django admin
    path("admin/", admin.site.urls),

    # Root URL → charts landing page
    path("", charts_views.landing_page, name="landing"),

    # All charts-related pages under /charts/
    path("charts/", include("charts.urls")),
]
