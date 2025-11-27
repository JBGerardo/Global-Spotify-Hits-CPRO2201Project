"""
Django views for the Global Spotify Hits project (CPRO 2201 - Python II).

This file handles the logic for:
1. Fetching data from the database (ChartEntry model).
2. Aggregating data (Counts, Sums) for analysis.
3. Generating charts using the helper in utils.py.
4. Rendering HTML templates with the data.
"""

from django.core.paginator import Paginator
from django.db.models import Count, Sum, Q
from django.shortcuts import render

# Import models
from .models import ChartEntry

# Import our custom chart styling utility
from .utils import get_spotify_chart

import matplotlib
# Use a non-interactive backend so Matplotlib can run on the server
# without needing a display (standard for Django projects).
matplotlib.use("Agg")


# ---------- Country label helpers ----------

# Mapping from country code to a human-friendly label.
COUNTRY_LABELS = {
    "global": "Global",
    "us": "United States (US)",
    "gb": "United Kingdom (GB)",
    "ca": "Canada (CA)",
    "au": "Australia (AU)",
    "de": "Germany (DE)",
    "fr": "France (FR)",
    "br": "Brazil (BR)",
    "mx": "Mexico (MX)",
    "jp": "Japan (JP)",
    "ng": "Nigeria (NG)",
    "fi": "Finland (FI)",
    "ch": "Switzerland (CH)",
    "no": "Norway (NO)",
    "se": "Sweden (SE)",
    "dk": "Denmark (DK)",
    "lu": "Luxembourg (LU)",
    # Other codes will fallback to uppercase
}


def code_upper(code_lower: str) -> str:
    """Helper: convert a country code string to uppercase safely."""
    try:
        return code_lower.upper()
    except AttributeError:
        return code_lower


def pretty_country(code: str) -> str:
    """Return a human-readable country name for a given country code."""
    if not code:
        return ""
    code_lower = str(code).lower()
    return COUNTRY_LABELS.get(code_lower, code_upper(code_lower))


# ---------- Views ----------


def landing_page(request):
    """
    Simple landing page that introduces the project.
    """
    return render(request, "charts/landing.html", {"active_page": "home"})


def top_streams(request):
    """
    View: Top Tracks by Total Streams (2023)
    """
    # 1. Aggregate total streams per track
    qs = (
        ChartEntry.objects.values("track_name", "artist")
        .annotate(total_streams=Sum("streams"))
        .order_by("-total_streams")[:10]
    )

    # 2. Prepare data for the chart
    labels = [f"{row['track_name']} – {row['artist']}" for row in qs]
    values = [row["total_streams"] for row in qs]

    # 3. Generate Spotify-styled chart
    chart_image = get_spotify_chart(
        labels=labels,
        values=values,
        title="Top 10 Tracks by Total Streams",
        xlabel="Total Streams",
        orientation='h'
    )

    context = {
        "active_page": "top_streams",
        "tracks": qs,
        "chart_image": chart_image,
    }
    return render(request, "charts/top_streams.html", context)


def top_songs_by_countries(request):
    """
    View: Top Songs by Number of Countries Appeared In (2023)
    """
    # 1. Count distinct countries per track
    qs = (
        ChartEntry.objects.values("track_name", "artist")
        .annotate(country_count=Count("country", distinct=True))
        .order_by("-country_count")[:20]
    )

    # 2. Prepare data for chart (Top 10 only)
    top_for_chart = list(qs[:10])
    labels = [f"{row['track_name']} – {row['artist']}" for row in top_for_chart]
    values = [row["country_count"] for row in top_for_chart]

    # 3. Generate Spotify-styled chart
    chart_image = get_spotify_chart(
        labels=labels,
        values=values,
        title="Global Reach: Top 10 Hits by Country Count",
        xlabel="Number of Countries",
        orientation='h'
    )

    context = {
        "active_page": "top_songs",
        "songs": qs,
        "chart_image": chart_image,
    }
    return render(request, "charts/top_songs_by_countries.html", context)


def country_diversity(request):
    """
    View: Country Chart Diversity (2023)
    """
    # 1. Count unique tracks per country
    base_qs = ChartEntry.objects.values("country")
    diversity_qs = (
        base_qs.annotate(unique_tracks=Count("track_id", distinct=True))
        .order_by("-unique_tracks")[:10]
    )

    # 2. Build rows with pretty names
    diversity_rows = [
        {
            "country_label": pretty_country(row["country"]),
            "unique_tracks": row["unique_tracks"],
        }
        for row in diversity_qs
    ]

    # 3. Prepare data for chart
    countries = [row["country_label"] for row in diversity_rows]
    values = [row["unique_tracks"] for row in diversity_rows]

    # 4. Generate chart (Vertical for diversity comparison)
    chart_image = get_spotify_chart(
        labels=countries,
        values=values,
        title="Market Diversity: Unique Tracks per Country",
        xlabel="Unique Tracks Count",
        orientation='v'  # Vertical bars look better for country names
    )

    context = {
        "active_page": "country_diversity",
        "diversity_rows": diversity_rows,
        "chart_image": chart_image,
    }
    return render(request, "charts/country_diversity.html", context)


def chart_browser(request):
    """
    View: Raw 2023 chart entries with filters and pagination.
    """
    qs = ChartEntry.objects.all().order_by("-date", "position")

    # -------- Dropdown options for filters --------
    country_codes = (
        ChartEntry.objects.values_list("country", flat=True)
        .distinct()
        .order_by("country")
    )
    countries = [
        {"code": c, "label": pretty_country(c)}
        for c in country_codes
        if c is not None
    ]

    month_names = ["January", "February", "March", "April", "May", "June", 
                   "July", "August", "September", "October", "November", "December"]
    months = [{"value": i + 1, "label": month_names[i]} for i in range(12)]

    # -------- Read filter values --------
    country_query = request.GET.get("country", "").strip()
    month_query = request.GET.get("month", "").strip()
    search_query = request.GET.get("search", "").strip()
    explicit_only = request.GET.get("explicit_only") is not None

    # -------- Apply filters --------
    if country_query:
        qs = qs.filter(country__iexact=country_query)

    if month_query:
        try:
            month_int = int(month_query)
            qs = qs.filter(date__month=month_int)
        except ValueError:
            pass

    if search_query:
        qs = qs.filter(
            Q(track_name__icontains=search_query)
            | Q(artist__icontains=search_query)
        )

    if explicit_only:
        qs = qs.filter(explicit=True)

    # -------- Pagination --------
    paginator = Paginator(qs, 50)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Attach pretty_country labels
    for entry in page_obj.object_list:
        entry.pretty_country = pretty_country(entry.country)

    context = {
        "active_page": "browser",
        "page_obj": page_obj,
        "countries": countries,
        "months": months,
        "country_query": country_query,
        "month_query": month_query,
        "search_query": search_query,
        "explicit_only": explicit_only,
    }
    return render(request, "charts/chart_browser.html", context)