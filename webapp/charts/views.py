# webapp/charts/views.py

import base64
import io

from django.core.paginator import Paginator
from django.db.models import Count, Sum, Q
from django.shortcuts import render

from .models import ChartEntry

import matplotlib

# Use non-interactive backend for server-side image generation
matplotlib.use("Agg")
import matplotlib.pyplot as plt


# ---------- Country label helpers ----------

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
    try:
        return code_lower.upper()
    except Exception:
        return str(code_lower)


def pretty_country(code: str) -> str:
    if not code:
        return ""
    code_lower = str(code).lower()
    return COUNTRY_LABELS.get(code_lower, code_upper(code_lower))


# ---------- Matplotlib helper ----------


def render_matplotlib_figure(fig) -> str:
    """
    Convert a Matplotlib figure to a base64 string for embedding in <img src="...">.
    """
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    buf.seek(0)
    image_base64 = base64.b64encode(buf.read()).decode("ascii")
    plt.close(fig)
    return image_base64


# ---------- Views ----------


def landing_page(request):
    """
    Simple landing page that introduces the project and links to the main analysis pages.
    """
    return render(request, "charts/landing.html")


def top_streams(request):
    """
    View: Top Tracks by Total Streams (global 2023)
    Aggregates total streams per track_name + artist and shows a bar chart + table.
    """
    qs = (
        ChartEntry.objects.values("track_name", "artist")
        .annotate(total_streams=Sum("streams"))
        .order_by("-total_streams")[:10]
    )

    labels = [f"{row['track_name']} – {row['artist']}" for row in qs]
    values = [row["total_streams"] for row in qs]

    # Slightly smaller figure and text to keep within the card
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.barh(labels, values)
    ax.set_title("Top 10 Tracks by Total Streams (2023)", fontsize=11)
    ax.set_xlabel("Total Streams", fontsize=10)
    ax.tick_params(axis="y", labelsize=8)
    ax.invert_yaxis()
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
    Shows how globally distributed each hit is.
    """
    qs = (
        ChartEntry.objects.values("track_name", "artist")
        .annotate(country_count=Count("country", distinct=True))
        .order_by("-country_count")[:20]
    )

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
        "songs": qs,
        "chart_image": chart_image,
    }
    return render(request, "charts/top_songs_by_countries.html", context)


def country_diversity(request):
    """
    View: Country Chart Diversity
    Counts how many unique tracks appeared in each country's 2023 charts.
    """
    diversity_qs = (
        ChartEntry.objects.values("country")
        .annotate(unique_tracks=Count("track_id", distinct=True))
        .order_by("-unique_tracks")[:10]
    )

    # Build rows with pretty country labels
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
    ax.set_title(
        "Top 10 Countries by Chart Diversity (Unique Tracks, 2023)",
        fontsize=11,
    )
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
    Filters:
    - country
    - month (1–12)
    - free text search (track_name / artist)
    - explicit-only flag
    """
    qs = ChartEntry.objects.all().order_by("-date", "position")

    # Country choices
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

    # Month choices for 2023
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

    # Read filters
    country_query = request.GET.get("country", "").strip()
    month_query = request.GET.get("month", "").strip()
    search_query = request.GET.get("search", "").strip()
    explicit_only = request.GET.get("explicit_only") is not None

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

    # Pagination
    paginator = Paginator(qs, 50)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Attach pretty_country for template
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
