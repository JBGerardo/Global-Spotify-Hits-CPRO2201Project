from io import BytesIO
import base64

from django.shortcuts import render
from django.core.paginator import Paginator

import matplotlib
matplotlib.use("Agg")  # non-GUI backend for server use
import matplotlib.pyplot as plt

from analysis.spotify_analysis import (
    load_spotify_charts,
    compute_country_song_counts,
    compute_chart_diversity_by_country,
)
from charts.models import ChartEntry

CSV_NAME = "charts_2023.csv"  # make sure this matches the filename in data/raw


# Simple mapping from ISO-like codes to human-readable country names.
# We don't need every country in the world, just the ones that might appear.
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
    }
    return render(request, "charts/top_songs_by_countries.html", context)


def country_diversity(request):
    """
    View: show top 10 countries by chart diversity (unique tracks),
    and render a Matplotlib bar chart.
    """
    df = load_spotify_charts(CSV_NAME)
    diversity_df = compute_chart_diversity_by_country(df).head(10)

    # Use pretty labels for the chart, but keep codes in DB
    countries_raw = diversity_df["country"].tolist()
    countries = [pretty_country_label(code) for code in countries_raw]
    unique_tracks = diversity_df["unique_tracks"].tolist()

    # --- Create Matplotlib figure ---
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(countries, unique_tracks)
    ax.set_title("Top 10 Countries by Chart Diversity (Unique Tracks)")
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

    # Also pass pretty labels to the table
    diversity_rows = diversity_df.to_dict(orient="records")
    for row in diversity_rows:
        row["country_label"] = pretty_country_label(row["country"])

    context = {
        "diversity_rows": diversity_rows,
        "chart_image": chart_base64,
    }
    return render(request, "charts/country_diversity.html", context)


def chart_browser(request):
    """
    View: browse raw ChartEntry rows from SQLite with
    simple filtering (by country) and pagination.
    """
    country_query = (request.GET.get("country") or "").strip()

    qs = ChartEntry.objects.all().order_by("country", "date", "position")

    if country_query:
        qs = qs.filter(country__iexact=country_query)

    paginator = Paginator(qs, 25)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Distinct country codes from DB
    country_codes = (
        ChartEntry.objects.values_list("country", flat=True)
        .distinct()
        .order_by("country")
    )

    # Build list of {code, label} for the dropdown
    countries = [
        {
            "code": code,
            "label": pretty_country_label(code),
        }
        for code in country_codes
    ]

    # Add pretty labels to table rows, too
    for entry in page_obj.object_list:
        entry.pretty_country = pretty_country_label(entry.country)

    context = {
        "page_obj": page_obj,
        "country_query": country_query,
        "countries": countries,
    }
    return render(request, "charts/chart_browser.html", context)
