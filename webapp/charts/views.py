"""
Django views for the Global Spotify Hits project (CPRO 2201 - Python II).
Updated to use pycountry for accurate full country names.
"""

import pycountry
from django.core.paginator import Paginator
from django.db.models import Count, Sum, Q
from django.shortcuts import render

# Import models
from .models import ChartEntry

# Import our custom chart styling utility
from .utils import get_spotify_chart

import matplotlib
# Use a non-interactive backend so Matplotlib can run on the server
matplotlib.use("Agg")


# ---------- Country label helpers ----------

def pretty_country(code: str) -> str:
    """
    Return a human-readable country name for a given country code.
    Uses pycountry library with manual overrides for specific cases.
    """
    if not code:
        return ""
    
    code = str(code).strip().upper()

    # 1. Manual Overrides (for "Global" or distinct naming preferences)
    overrides = {
        "GLOBAL": "Global",
        "GB": "United Kingdom",
        "US": "United States",
        "KR": "South Korea",
        "VN": "Vietnam",
        "KZ": "Kazakhstan",
        "AE": "United Arab Emirates",
    }
    
    if code in overrides:
        return overrides[code]

    # 2. Try looking up in the ISO database via pycountry
    try:
        country = pycountry.countries.get(alpha_2=code)
        if country:
            return country.name
    except LookupError:
        pass

    # 3. Fallback: just return the code (e.g., "XYZ")
    return code


# ---------- Views ----------

def landing_page(request):
    """Simple landing page that introduces the project."""
    return render(request, "charts/landing.html", {"active_page": "home"})


def top_streams(request):
    """View: Top Tracks by Total Streams (2023)"""

    # Helper for numbers (1.2M, 500K)
    def humanize(num):
        num = float(num)
        if num >= 1_000_000_000:
            return f"{num/1_000_000_000:.2f}B"
        if num >= 1_000_000:
            return f"{num/1_000_000:.1f}M"
        if num >= 1_000:
            return f"{num/1_000:.1f}K"
        return str(int(num))

    # 1. Fetch TOP 20 for the TABLE
    full_qs = (
        ChartEntry.objects.values("track_name", "artist")
        .annotate(total_streams=Sum("streams"))
        .order_by("-total_streams")[:20]
    )

    # 2. Extract TOP 10 for the CHART
    top10 = full_qs[:10]

    # 3. Chart Data
    labels = [f"{row['track_name']} – {row['artist']}" for row in top10]
    values = [row["total_streams"] for row in top10]

    chart_image = get_spotify_chart(
        labels=labels,
        values=values,
        title="Top 10 Tracks by Total Streams",
        xlabel="Total Streams",
        orientation='h'
    )

    # 4. Build list for TABLE
    tracks = []
    for row in full_qs:
        tracks.append({
            "track_name": row["track_name"],
            "artist": row["artist"],
            "total_streams": row["total_streams"],
            "formatted_streams": humanize(row["total_streams"])
        })

    context = {
        "active_page": "top_streams",
        "tracks": tracks,
        "chart_image": chart_image,
    }
    return render(request, "charts/top_streams.html", context)


def top_songs_by_countries(request):
    """View: Top Songs by Number of Countries Appeared In (2023)"""
    
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
    """View: Country Chart Diversity (2023)"""

    # 1. ALL countries for the TABLE
    all_qs = (
        ChartEntry.objects.values("country")
        .annotate(unique_tracks=Count("track_id", distinct=True))
        .order_by("-unique_tracks")
    )

    # Convert to full names using our global pretty_country helper
    all_rows = [
        {
            "country_label": pretty_country(row["country"]),
            "unique_tracks": row["unique_tracks"],
        }
        for row in all_qs
    ]

    # 2. TOP 10 for the CHART
    top10 = all_rows[:10]
    chart_countries = [row["country_label"] for row in top10]
    chart_values = [row["unique_tracks"] for row in top10]

    # 3. Generate CHART
    chart_image = get_spotify_chart(
        labels=chart_countries,
        values=chart_values,
        title="Market Diversity: Top 10 Countries with Most Unique Charting Tracks",
        xlabel="Unique Tracks Count",
        orientation="v"
    )

    context = {
        "active_page": "country_diversity",
        "diversity_rows": all_rows,
        "chart_image": chart_image,
    }

    return render(request, "charts/country_diversity.html", context)


def chart_browser(request):
    """View: Raw 2023 chart entries with filters and pagination."""
    
    qs = ChartEntry.objects.all().order_by("-date", "position")

    # -------- Dropdown options for filters --------
    country_codes = (
        ChartEntry.objects.values_list("country", flat=True)
        .distinct()
        .order_by("country")
    )

    # Normalize & map all dropdown country names
    countries = []
    for c in country_codes:
        if not c:
            continue
        
        # Use our helper to get the FULL NAME
        full_name = pretty_country(c)
        countries.append({"code": c.strip().upper(), "label": full_name})

    # Sort A→Z alphabetically by the LABEL (Full Name)
    countries = sorted(countries, key=lambda x: x["label"])

    # Month dropdown options
    month_names = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ]
    months = [{"value": i + 1, "label": month_names[i]} for i in range(12)]

    # -------- Read Filters --------
    country_query = (request.GET.get("country", "") or "").strip().upper()
    month_query = request.GET.get("month", "").strip()
    search_query = request.GET.get("search", "").strip()
    explicit_only = request.GET.get("explicit_only") is not None

    # -------- Apply Filters --------
    if country_query:
        qs = qs.filter(country__iexact=country_query)

    if month_query.isdigit():
        qs = qs.filter(date__month=int(month_query))

    if search_query:
        qs = qs.filter(
            Q(track_name__icontains=search_query) |
            Q(artist__icontains=search_query)
        )

    if explicit_only:
        qs = qs.filter(explicit=True)

    # -------- Pagination --------
    paginator = Paginator(qs, 50)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # -------- Format table display --------
    # This ensures the table rows show "United Arab Emirates" instead of "AE"
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