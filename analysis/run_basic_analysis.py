"""
run_basic_analysis.py

Quick script to test our analysis functions on charts_2023.csv.

It prints:
- basic dataset info
- top songs by number of countries
- chart diversity per country
- top songs by total streams
"""

from analysis.spotify_analysis import (
    load_spotify_charts,
    compute_country_song_counts,
    compute_chart_diversity_by_country,
    compute_average_days_on_chart,
    compute_top_songs_by_streams,
)

CSV_NAME = "charts_2023.csv"  # <- change if your file name is different


def main():
    # Load data
    df = load_spotify_charts(CSV_NAME)
    print("=== RAW DATA ===")
    print("Rows:", len(df))
    print("Columns:", list(df.columns))
    print()

    # 1) In how many countries does each song appear?
    try:
        print("=== Top 10 songs by number of countries ===")
        country_counts = compute_country_song_counts(df)
        print(country_counts.head(10))
        print()
    except Exception as exc:
        print("[WARN] Could not compute country counts:", exc)
        print()

    # 2) How diverse is each country's chart?
    try:
        print("=== Top 10 countries by chart diversity (unique tracks) ===")
        diversity = compute_chart_diversity_by_country(df)
        print(diversity.head(10))
        print()
    except Exception as exc:
        print("[WARN] Could not compute chart diversity:", exc)
        print()

    # 3) How long do tracks stay on the chart?
    try:
        print("=== Top 10 tracks by days on chart ===")
        days_on_chart = compute_average_days_on_chart(df)
        print(days_on_chart.head(10))
        print()
    except Exception as exc:
        print("[WARN] Could not compute days on chart:", exc)
        print()

    # 4) Top songs by total streams
    try:
        print("=== Top 10 songs by total streams ===")
        top_streams = compute_top_songs_by_streams(df, n=10)
        print(top_streams)
        print()
    except Exception as exc:
        print("[WARN] Could not compute top songs by streams:", exc)
        print()


if __name__ == "__main__":
    main()
