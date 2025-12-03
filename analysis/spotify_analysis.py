"""spotify_analysis.py
"""

from pathlib import Path

import pandas as pd

# Base directory for the CSV files:
# .../Global-Spotify-Hits-CPRO2201Project-main/data/raw
DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"


def load_spotify_charts(csv_name):
    """Load the Spotify charts CSV from ``data/raw``.

    Parameters
    ----------
    csv_name : str
        File name inside the ``data/raw`` folder,
        for example: ``"charts_2023.csv"``.

    Returns
    -------
    pandas.DataFrame
        DataFrame with cleaned column names such as
        ``track_name``, ``artist``, ``country``, ``date``,
        ``position`` and ``streams``.

    """

    # 1) Build the full path to the CSV file.
    csv_path = DATA_DIR / csv_name

    # 2) Fail early with a clear error if the file does not exist.
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV not found at: {csv_path}")

    # 3) Read the CSV file into a DataFrame.
    df = pd.read_csv(csv_path)

    # 4) Normalise the column names so that the rest of the code
    #    can use the same names every time.
    rename_map = {
        "name": "track_name",
        "artists": "artist",
        "artist_genres": "artist_genres",
        "duration": "duration",
        "explicit": "explicit",
        "country": "country",
        "date": "date",
        "position": "position",
        "streams": "streams",
        "track_id": "track_id",
    }

    # Only rename columns that are actually present in the CSV.
    for old_name, new_name in rename_map.items():
        if old_name in df.columns:
            df = df.rename(columns={old_name: new_name})

    # 5) Convert the date column to a real datetime type if it exists.
    #    This will make any date filtering or grouping much easier.
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")

    return df


def _ensure_columns(df, required_cols):
    """Small helper to check that required columns exist.

    If any column is missing we raise a ValueError with a friendly message.
    """
    missing = set(required_cols) - set(df.columns)
    if missing:
        missing_list = ", ".join(sorted(missing))
        raise ValueError(f"Missing required columns: {missing_list}")


def compute_country_song_counts(df):
    """For each song, count how many countries it appears in.

    Expected columns in ``df``:
    - ``track_name``
    - ``artist``
    - ``country``

    Returns a DataFrame with:
    - ``track_name``
    - ``artist``
    - ``country_count`` (how many different countries played the song)
    """

    _ensure_columns(df, ["track_name", "artist", "country"])

    # 1) Keep only the columns we actually need.
    subset = df[["track_name", "artist", "country"]].copy()

    # 2) Remove duplicate rows so that we only count each
    #    (track, artist, country) combination once.
    subset = subset.drop_duplicates()

    # 3) Group by song (track + artist) and count how many
    #    different countries each song appears in.
    grouped = (
        subset.groupby(["track_name", "artist"])["country"]
        .nunique()
        .reset_index(name="country_count")
        .sort_values("country_count", ascending=False)
    )

    return grouped


def compute_chart_diversity_by_country(df):
    """For each country, calculate how many unique tracks appear.

    Expected columns in ``df``:
    - ``track_name``
    - ``country``

    Returns a DataFrame with:
    - ``country``
    - ``unique_tracks`` (number of distinct tracks in that country)
    """

    _ensure_columns(df, ["track_name", "country"])

    # 1) Keep only the needed columns.
    subset = df[["track_name", "country"]].copy()

    # 2) Drop any duplicate (country, track_name) pairs.
    subset = subset.drop_duplicates()

    # 3) Group by country and count how many unique songs appear.
    diversity = (
        subset.groupby("country")["track_name"]
        .nunique()
        .reset_index(name="unique_tracks")
        .sort_values("unique_tracks", ascending=False)
    )

    return diversity


def compute_average_days_on_chart(df):
    """Estimate how long tracks stay on the chart (distinct days).

    Expected columns in ``df``:
    - ``track_name``
    - ``artist``
    - ``date``

    Returns a DataFrame with:
    - ``track_name``
    - ``artist``
    - ``days_on_chart`` (number of distinct dates this song appears on)
    """

    _ensure_columns(df, ["track_name", "artist", "date"])

    # 1) Remove rows where the date is missing.
    clean_df = df.dropna(subset=["date"]).copy()

    # 2) Group by song and count how many distinct dates we see.
    duration = (
        clean_df.groupby(["track_name", "artist"])["date"]
        .nunique()
        .reset_index(name="days_on_chart")
        .sort_values("days_on_chart", ascending=False)
    )

    return duration


def compute_top_songs_by_streams(df, n=20):
    """Compute the top ``n`` songs by total streams across all countries.

    Expected columns in ``df``:
    - ``track_name``
    - ``artist``
    - ``streams``

    Returns a DataFrame with:
    - ``track_name``
    - ``artist``
    - ``total_streams`` (sum of ``streams`` for that song)
    """

    _ensure_columns(df, ["track_name", "artist", "streams"])

    # 1) Group by song and sum the streams.
    totals = (
        df.groupby(["track_name", "artist"])["streams"]
        .sum()
        .reset_index(name="total_streams")
        .sort_values("total_streams", ascending=False)
    )

    # 2) Return only the top N songs.
    return totals.head(n)


if __name__ == "__main__":
    # Simple manual test so that we can run:
    #     python spotify_analysis.py
    # and quickly see if our functions behave as expected.

    test_file = "charts_2023.csv"
    print(f"DATA_DIR = {DATA_DIR}")

    try:
        df_test = load_spotify_charts(test_file)
        print("Loaded DataFrame shape:", df_test.shape)
        print("Columns:", list(df_test.columns))
        print()

        print("=== Top 5 songs by number of countries ===")
        print(compute_country_song_counts(df_test).head(5))
        print()

        print("=== Chart diversity by country (top 5) ===")
        print(compute_chart_diversity_by_country(df_test).head(5))
        print()

        print("=== Average days on chart (top 5) ===")
        print(compute_average_days_on_chart(df_test).head(5))
        print()

        print("=== Top 5 songs by total streams ===")
        print(compute_top_songs_by_streams(df_test, n=5))
        print()
    except FileNotFoundError as exc:
        print(exc)
