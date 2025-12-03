from django.contrib import admin
from .models import ChartEntry


@admin.register(ChartEntry)
class ChartEntryAdmin(admin.ModelAdmin):
    """
    Admin configuration for ChartEntry.

    This makes it easy to:
    - browse chart entries
    - filter by country, date, explicit flag
    - search by track name, artist, or track ID
    """

    list_display = (
        "date",
        "country",
        "position",
        "track_name",
        "artist",
        "streams",
        "explicit",
    )
    list_filter = ("country", "date", "explicit")
    search_fields = ("track_name", "artist", "track_id")
    ordering = ("country", "-date", "position")
