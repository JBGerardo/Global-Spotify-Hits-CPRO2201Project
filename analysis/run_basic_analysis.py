"""
run_basic_analysis.py

Quick script to test our analysis functions on charts_2023.csv.

It prints:
- basic dataset info
- top songs by number of countries
- chart diversity per country
- top songs by total streams

This script is written in a simple, step-by-step style to match
the level of CPRO 2201 (Python II).
"""

# Import the analysis functions from the file in the same folder.
# Because run_basic_analysis.py and spotify_analysis.py are both inside
# the "analysis" directory, we can import directly from spotify_analysis.
from spotify_analysis import (
    load_spotify_charts,
    compute_country_song_counts,
    compute_chart_diversity_by_country,
    compute_average_days_on_chart,
    compute_top_songs_by_streams,
)


def main():
    """Run a basic analysis on the charts_2023.csv file.

    This function demonstrates how to:
    - load the data
    - inspect basic information
    - compute several summary tables
    """

    # 1) Name of the CSV file we want to analyze.
    #    The load_spotify_charts function will look for this file
    #    inside the data/raw directory at the project root.
    csv_name = "charts_2023.csv"

    # 2) Load the DataFrame using our helper function.
    try:
        df = load_spotify_charts(csv_name)
    except FileNotFoundError as exc:
        print("[ERROR] Could not find the CSV file:", exc)
        return

    # 3) Print some basic information about the dataset.
    print("=== Basic dataset info ===")
    print("Shape (rows, columns):", df.shape)
    print("Columns:", list(df.columns))
    print()

    # Optionally, you could also show the first few rows:
    # print(df.head())
    # print()

    # 4) Top songs by number of countries they appear in.
    try:
        print("=== Top 10 songs by number of countries ===")
        song_country_counts = compute_country_song_counts(df)
        print(song_country_counts.head(10))
        print()
    except Exception as exc:
        print("[WARN] Could not compute country song counts:", exc)
        print()

    # 5) Chart diversity per country (how many unique tracks).
    try:
        print("=== Chart diversity per country (top 10) ===")
        diversity = compute_chart_diversity_by_country(df)
        print(diversity.head(10))
        print()
    except Exception as exc:
        print("[WARN] Could not compute chart diversity:", exc)
        print()

    # 6) Average days on chart per song (approximate).
    try:
        print("=== Songs with most days on chart (top 10) ===")
        days_on_chart = compute_average_days_on_chart(df)
        print(days_on_chart.head(10))
        print()
    except Exception as exc:
        print("[WARN] Could not compute days on chart:", exc)
        print()

    # 7) Top songs by total streams (across all countries).
    try:
        print("=== Top 10 songs by total streams ===")
        top_streams = compute_top_songs_by_streams(df, n=10)
        print(top_streams)
        print()
    except Exception as exc:
        print("[WARN] Could not compute top songs by streams:", exc)
        print()


if __name__ == "__main__":
    # When we run this file directly with:
    #     python run_basic_analysis.py
    # the main() function will be executed.
    main()
