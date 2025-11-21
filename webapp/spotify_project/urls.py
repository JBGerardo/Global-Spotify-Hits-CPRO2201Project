from django.contrib import admin
from django.urls import path, include

from charts import views as charts_views

urlpatterns = [
    path("admin/", admin.site.urls),
    # Home / landing page
    path("", charts_views.landing_page, name="landing_page"),
    # Charts app routes
    path("charts/", include("charts.urls")),
]
