# webapp/charts/views.py
"""
Django views for the Global Spotify Hits project (CPRO 2201 - Python II).

This file is written in a clear, step-by-step style to match the course level.
Each view does a small, focused task and uses Django ORM queries that are
similar to what we saw in the Django CRUD and templates notes:

- We use ChartEntry.objects.filter(...) / .values(...) to fetch data.
- We use aggregate helpers like Count and Sum to compute summary values.
- We use simple function-based views that call render(...) with a context dict.
"""

import base64
import io

from django.core.paginator import Paginator
from django.db.models import Count, Sum, Q
from django.shortcuts import render

from .models import ChartEntry

import matplotlib

# Use a non-interactive backend so Matplotlib can run on the server
# without needing a display (this is standard in Django projects).
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402  (import after setting backend)


# ---------- Country label helpers ----------


# Mapping from country code in the CSV to a human-friendly label.
# We only list a few common codes; any others fall back to the uppercased code.
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
    # Any other code falls back to uppercased code
}


def code_upper(code_lower: str) -> str:
    """
    Helper: convert a country code string to uppercase safely.
    """
    try:
        return code_lower.upper()
    except AttributeError:
        # If code_lower is None or not a string we just return it unchanged.
        return code_lower


def pretty_country(code: str) -> str:
    """
    Return a human-readable country name for a given country code.

    Examples:
    - "us"  -> "United States (US)"
    - "ca"  -> "Canada (CA)"
    - "xyz" -> "XYZ"  (fallback to uppercased code)
    """
    if not code:
        return ""
    code_lower = str(code).lower()
    return COUNTRY_LABELS.get(code_lower, code_upper(code_lower))


# ---------- Matplotlib helper ----------


def render_matplotlib_figure(fig) -> str:
    """
    Convert a Matplotlib figure to a base64 string.

    We create a BytesIO buffer, save the figure as PNG into that buffer,
    then base64-encode the result. The template can then embed the chart as:

        <img src="data:image/png;base64,{{ chart_image }}" ... />

    This is a standard pattern when using Matplotlib with Django templates.
    """
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    buf.seek(0)
    image_base64 = base64.b64encode(buf.read()).decode("ascii")
    plt.close(fig)  # free the figure so we do not leak memory
    return image_base64


# ---------- Views ----------


def landing_page(request):
    """
    Simple landing page that introduces the project and links to the main analysis pages.
    """
    return render(request, "charts/landing.html")


def top_streams(request):
    """
    View: Top Tracks by Total Streams (2023)

    For each (track_name, artist) pair we sum up all the streams across
    all available countries and dates. We then:
    - show a bar chart (top 10 songs)
    - show a table with the same data
    """
    # Step 1: Build a base queryset grouped by track and artist.
    base_qs = ChartEntry.objects.values("track_name", "artist")

    # Step 2: Use annotate + Sum to compute total streams per song.
    qs = (
        base_qs.annotate(total_streams=Sum("streams"))
        .order_by("-total_streams")[:10]
    )

    # Step 3: Prepare labels and values for the bar chart.
    labels = [f"{row['track_name']} – {row['artist']}" for row in qs]
    values = [row["total_streams"] for row in qs]

    # Step 4: Create the Matplotlib figure.
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.barh(labels, values)
    ax.set_title("Top 10 Tracks by Total Streams (2023)", fontsize=11)
    ax.set_xlabel("Total Streams", fontsize=10)
    ax.tick_params(axis="y", labelsize=8)
    ax.invert_yaxis()  # highest value at the top
    plt.tight_layout()

    chart_image = render_matplotlib_figure(fig)

    context = {
        "tracks": qs,
        "chart_image": chart_image,
    }
    return render(request, "charts/top_streams.html", context)


def top_songs_by_countries(request):
    """
    View: Top Songs by Number of Countries Appeared In (2023)

    For each (track_name, artist) pair we count in how many different
    countries it appears. This is one way to measure how "global" a hit is.
    """
    # Step 1: Base queryset grouped by track and artist.
    base_qs = ChartEntry.objects.values("track_name", "artist")

    # Step 2: Count distinct countries per song.
    qs = (
        base_qs.annotate(country_count=Count("country", distinct=True))
        .order_by("-country_count")[:20]
    )

    # Step 3: Prepare data for the chart (top 10 for the bar chart).
    top_for_chart = list(qs[:10])
    labels = [f"{row['track_name']} – {row['artist']}" for row in top_for_chart]
    values = [row["country_count"] for row in top_for_chart]

    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.barh(labels, values)
    ax.set_title("Top 10 Global Hits by Number of Countries (2023)", fontsize=11)
    ax.set_xlabel("Number of Countries", fontsize=10)
    ax.tick_params(axis="y", labelsize=8)
    ax.invert_yaxis()
    plt.tight_layout()

    chart_image = render_matplotlib_figure(fig)

    context = {
        "songs": qs,  # full top 20 shown in the table
        "chart_image": chart_image,
    }
    return render(request, "charts/top_songs_by_countries.html", context)


def country_diversity(request):
    """
    View: Country Chart Diversity (2023)

    For each country we count how many different tracks appeared in its charts.
    This gives an idea of how diverse each country's Spotify chart is.
    """
    # Step 1: Group by country and count distinct track_id per country.
    base_qs = ChartEntry.objects.values("country")
    diversity_qs = (
        base_qs.annotate(unique_tracks=Count("track_id", distinct=True))
        .order_by("-unique_tracks")[:10]
    )

    # Step 2: Build rows with pretty labels for the template and chart.
    diversity_rows = [
        {
            "country_label": pretty_country(row["country"]),
            "unique_tracks": row["unique_tracks"],
        }
        for row in diversity_qs
    ]

    countries = [row["country_label"] for row in diversity_rows]
    values = [row["unique_tracks"] for row in diversity_rows]

    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.bar(countries, values)
    ax.set_title("Chart Diversity by Country (Unique Tracks, 2023)", fontsize=11)
    ax.set_xlabel("Country", fontsize=10)
    ax.set_ylabel("Number of Unique Tracks", fontsize=10)
    ax.tick_params(axis="x", labelsize=8)
    ax.tick_params(axis="y", labelsize=9)
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()

    chart_image = render_matplotlib_figure(fig)

    context = {
        "diversity_rows": diversity_rows,
        "chart_image": chart_image,
    }
    return render(request, "charts/country_diversity.html", context)


def chart_browser(request):
    """
    View: Raw 2023 chart entries with filters and pagination.

    Users can:
    - filter by country
    - filter by month (1–12)
    - search by track or artist name (case-insensitive)
    - show only explicit tracks

    This view is similar in spirit to the "list with filters" pattern
    used in CRUD demos: we start from a base queryset and then apply
    filter conditions based on GET parameters.
    """
    # Base queryset: all chart entries, newest dates first.
    qs = ChartEntry.objects.all().order_by("-date", "position")

    # -------- Dropdown options for filters --------

    # Country choices (distinct country codes present in the data).
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

    # Month choices (1–12) with names for the dropdown.
    month_names = [
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December",
    ]
    months = [{"value": i + 1, "label": month_names[i]} for i in range(12)]

    # -------- Read filter values from request.GET --------

    country_query = request.GET.get("country", "").strip()
    month_query = request.GET.get("month", "").strip()
    search_query = request.GET.get("search", "").strip()
    explicit_only = request.GET.get("explicit_only") is not None

    # -------- Apply filters to the queryset --------

    # Filter by country code (exact match, ignoring case).
    if country_query:
        qs = qs.filter(country__iexact=country_query)

    # Filter by month (1–12). If month_query cannot be converted to int
    # we simply ignore it (no crash).
    if month_query:
        try:
            month_int = int(month_query)
            qs = qs.filter(date__month=month_int)
        except ValueError:
            pass

    # Free text search on track_name or artist (case-insensitive).
    if search_query:
        qs = qs.filter(
            Q(track_name__icontains=search_query)
            | Q(artist__icontains=search_query)
        )

    # Explicit-only toggle.
    if explicit_only:
        qs = qs.filter(explicit=True)

    # -------- Pagination --------

    paginator = Paginator(qs, 50)  # 50 rows per page
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Attach pretty_country for convenience in the template.
    for entry in page_obj.object_list:
        entry.pretty_country = pretty_country(entry.country)

    context = {
        "page_obj": page_obj,
        "countries": countries,
        "months": months,
        "country_query": country_query,
        "month_query": month_query,
        "search_query": search_query,
        "explicit_only": explicit_only,
    }
    return render(request, "charts/chart_browser.html", context)
