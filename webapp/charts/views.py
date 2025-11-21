from io import BytesIO
import base64

from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Q

import matplotlib
matplotlib.use("Agg")  # non-GUI backend for server use
import matplotlib.pyplot as plt

from analysis.spotify_analysis import (
    load_spotify_charts,
    compute_country_song_counts,
    compute_chart_diversity_by_country,
    compute_top_songs_by_streams,
)
from charts.models import ChartEntry

CSV_NAME = "charts_2023.csv"  # we are focusing on 2023 only

# Mapping from code -> human-readable country name
COUNTRY_NAME_MAP = {
    "au": "Australia",
    "ca": "Canada",
    "us": "United States",
    "gb": "United Kingdom",
    "de": "Germany",
    "fr": "France",
    "br": "Brazil",
    "mx": "Mexico",
    "jp": "Japan",
    "kr": "South Korea",
    "ph": "Philippines",
    "sg": "Singapore",
    "se": "Sweden",
    "no": "Norway",
    "fi": "Finland",
    "it": "Italy",
    "es": "Spain",
    "nl": "Netherlands",
    "dk": "Denmark",
    "be": "Belgium",
    "ch": "Switzerland",
    "ie": "Ireland",
    "nz": "New Zealand",
    "ar": "Argentina",
    "at": "Austria",
    "bg": "Bulgaria",
    "bo": "Bolivia",
    "by": "Belarus",
    "cl": "Chile",
    "co": "Colombia",
    "cr": "Costa Rica",
    "cz": "Czech Republic",
    "do": "Dominican Republic",
    "ec": "Ecuador",
    "ee": "Estonia",
    "gr": "Greece",
    "gt": "Guatemala",
    "hk": "Hong Kong",
    "hu": "Hungary",
    "id": "Indonesia",
    "il": "Israel",
    "in": "India",
    "is": "Iceland",
    "lt": "Lithuania",
    "lu": "Luxembourg",
    "lv": "Latvia",
    "my": "Malaysia",
    "ni": "Nicaragua",
    "pa": "Panama",
    "pe": "Peru",
    "pl": "Poland",
    "pt": "Portugal",
    "py": "Paraguay",
    "ro": "Romania",
    "ru": "Russia",
    "sa": "Saudi Arabia",
    "sk": "Slovakia",
    "sv": "El Salvador",
    "th": "Thailand",
    "tr": "Turkey",
    "tw": "Taiwan",
    "uy": "Uruguay",
    "ve": "Venezuela",
    "vn": "Vietnam",
    "za": "South Africa",
}

MONTH_LABELS = {
    1: "January",
    2: "February",
    3: "March",
    4: "April",
    5: "May",
    6: "June",
    7: "July",
    8: "August",
    9: "September",
    10: "October",
    11: "November",
    12: "December",
}


def pretty_country_label(code: str) -> str:
    """
    Turn a code like 'au' into 'Australia (au)'.
    If we don't know the code, fall back to 'AU (au)'.
    """
    if not code:
        return ""
    lower = code.lower()
    base_name = COUNTRY_NAME_MAP.get(lower, lower.upper())
    return f"{base_name} ({lower})"


def landing_page(request):
    """
    Simple landing page with Spotify-like black + green theme.
    Introduces the project and links to the main analysis pages.
    """
    context = {
        "active_page": "home",
    }
    return render(request, "charts/landing.html", context)


def top_songs_by_countries(request):
    """
    View: show the top 10 songs by the number of countries they appear in.
    Uses the Pandas-based analysis functions.
    """
    df = load_spotify_charts(CSV_NAME)
    country_counts = compute_country_song_counts(df).head(10)

    songs = country_counts.to_dict(orient="records")

    context = {
        "songs": songs,
        "row_count": len(country_counts),
        "active_page": "top_songs",
    }
    return render(request, "charts/top_songs_by_countries.html", context)


def top_songs_by_streams_view(request):
    """
    View: show the top 10 songs by total global streams.
    Uses Pandas + Matplotlib for a bar chart.
    """
    df = load_spotify_charts(CSV_NAME)
    top_streams_df = compute_top_songs_by_streams(df, n=10)

    labels = [
        f"{row.track_name} ({row.artist})"
        for row in top_streams_df.itertuples(index=False)
    ]
    values = top_streams_df["total_streams"].tolist()

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(labels, values)
    ax.set_title("Top 10 Songs by Total Global Streams (2023)")
    ax.set_xlabel("Song (Artist)")
    ax.set_ylabel("Total Streams")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()

    buffer = BytesIO()
    fig.savefig(buffer, format="png")
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()
    plt.close(fig)

    chart_base64 = base64.b64encode(image_png).decode("utf-8")

    context = {
        "songs": top_streams_df.to_dict(orient="records"),
        "chart_image": chart_base64,
        "active_page": "top_streams",
    }
    return render(request, "charts/top_streams.html", context)


def country_diversity(request):
    """
    View: show top 10 countries by chart diversity (unique tracks),
    and render a Matplotlib bar chart.
    """
    df = load_spotify_charts(CSV_NAME)
    diversity_df = compute_chart_diversity_by_country(df).head(10)

    countries_raw = diversity_df["country"].tolist()
    countries = [pretty_country_label(code) for code in countries_raw]
    unique_tracks = diversity_df["unique_tracks"].tolist()

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(countries, unique_tracks)
    ax.set_title("Top 10 Countries by Chart Diversity (Unique Tracks, 2023)")
    ax.set_xlabel("Country")
    ax.set_ylabel("Number of Unique Tracks")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()

    buffer = BytesIO()
    fig.savefig(buffer, format="png")
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()
    plt.close(fig)

    chart_base64 = base64.b64encode(image_png).decode("utf-8")

    diversity_rows = diversity_df.to_dict(orient="records")
    for row in diversity_rows:
        row["country_label"] = pretty_country_label(row["country"])

    context = {
        "diversity_rows": diversity_rows,
        "chart_image": chart_base64,
        "active_page": "country_diversity",
    }
    return render(request, "charts/country_diversity.html", context)


def chart_browser(request):
    """
    View: browse raw ChartEntry rows from SQLite with
    search + filtering (country, month, explicit) and pagination.

    We focus on the 2023 dataset, so we filter by month instead of year.
    """
    # --- Read filters from query params ---
    country_query = (request.GET.get("country") or "").strip()
    search_query = (request.GET.get("search") or "").strip()
    month_query = (request.GET.get("month") or "").strip()
    explicit_only = request.GET.get("explicit_only") == "on"

    # Base queryset
    qs = ChartEntry.objects.all().order_by("country", "date", "position")

    # Filter by country code
    if country_query:
        qs = qs.filter(country__iexact=country_query)

    # Search in track name OR artist
    if search_query:
        qs = qs.filter(
            Q(track_name__icontains=search_query)
            | Q(artist__icontains=search_query)
        )

    # Filter by month (1–12) — dataset is 2023 only
    if month_query:
        qs = qs.filter(date__month=month_query)

    # Explicit checkbox
    if explicit_only:
        qs = qs.filter(explicit=True)

    # Pagination (25 rows per page)
    paginator = Paginator(qs, 25)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Distinct countries (for dropdown)
    country_codes = (
        ChartEntry.objects.values_list("country", flat=True)
        .distinct()
        .order_by("country")
    )
    countries = [
        {"code": code, "label": pretty_country_label(code)}
        for code in country_codes
    ]

    # Distinct months (for dropdown)
    months_raw = (
        ChartEntry.objects.values_list("date__month", flat=True)
        .distinct()
        .order_by("date__month")
    )
    months = []
    for m in months_raw:
        if m is None:
            continue
        label = MONTH_LABELS.get(m, str(m))
        months.append({"value": m, "label": label})

    # Attach pretty labels on entries
    for entry in page_obj.object_list:
        entry.pretty_country = pretty_country_label(entry.country)

    context = {
        "page_obj": page_obj,
        "country_query": country_query,
        "search_query": search_query,
        "month_query": month_query,
        "explicit_only": explicit_only,
        "countries": countries,
        "months": months,
        "active_page": "browser",
    }
    return render(request, "charts/chart_browser.html", context)
