from django.shortcuts import render

from analysis.spotify_analysis import (
    load_spotify_charts,
    compute_country_song_counts,
)

CSV_NAME = "charts_2023.csv"  # make sure this matches your file name in data/raw


def top_songs_by_countries(request):
    """
    View: show the top 10 songs by the number of countries they appear in.
    """
    # Load data and compute stats
    df = load_spotify_charts(CSV_NAME)
    country_counts = compute_country_song_counts(df).head(10)

    # Convert DataFrame to a list of dicts for the template
    songs = country_counts.to_dict(orient="records")

    context = {
        "songs": songs,
        "row_count": len(country_counts),
    }
    return render(request, "charts/top_songs_by_countries.html", context)
