"""
spotify_analysis.py

Core data loading & analysis functions for the
Global Spotify Hits project (CPRO 2201 - Python II).

Works with a CSV that has columns:
  date, country, position, streams, track_id,
  artists, artist_genres, duration, explicit, name
"""

from pathlib import Path

import pandas as pd

# Base directory: .../Global-Spotify-Hits-Python II Project/data/raw
DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"


def load_spotify_charts(csv_name: str) -> pd.DataFrame:
    """
    Load the Spotify charts CSV from the data/raw directory
    and normalize column names for internal use.

    Parameters
    ----------
    csv_name : str
        e.g. 'charts_2023.csv'

    Returns
    -------
    pd.DataFrame with at least:
      - track_name
      - artist
      - country
      - date
      - position
      - streams
    """
    csv_path = DATA_DIR / csv_name
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV not found at: {csv_path}")

    df = pd.read_csv(csv_path)

    # Normalize columns: map original names -> internal names
    rename_map = {
        "name": "track_name",
        "artists": "artist",
        "country": "country",
        "date": "date",
        "position": "position",
        "streams": "streams",
    }

    # Only rename columns that actually exist
    existing_rename = {
        old: new for old, new in rename_map.items() if old in df.columns
    }
    df = df.rename(columns=existing_rename)

    # Ensure date is datetime
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")

    return df


def compute_country_song_counts(df: pd.DataFrame) -> pd.DataFrame:
    """
    For each song, count how many countries it appears in.

    Expects columns:
      - track_name
      - artist
      - country

    Returns
    -------
    pd.DataFrame with:
      - track_name
      - artist
      - country_count
    """
    required_cols = {"track_name", "artist", "country"}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(sorted(missing))}")

    grouped = (
        df.groupby(["track_name", "artist"])["country"]
        .nunique()
        .reset_index(name="country_count")
        .sort_values("country_count", ascending=False)
    )
    return grouped


def compute_chart_diversity_by_country(df: pd.DataFrame) -> pd.DataFrame:
    """
    For each country, calculate how many unique tracks appear.

    Expects columns:
      - track_name
      - country

    Returns
    -------
    pd.DataFrame with:
      - country
      - unique_tracks
    """
    required_cols = {"track_name", "country"}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(sorted(missing))}")

    diversity = (
        df.groupby("country")["track_name"]
        .nunique()
        .reset_index(name="unique_tracks")
        .sort_values("unique_tracks", ascending=False)
    )
    return diversity


def compute_average_days_on_chart(df: pd.DataFrame) -> pd.DataFrame:
    """
    Estimate how long tracks stay on the chart (distinct days).

    Expects columns:
      - track_name
      - artist
      - date

    Returns
    -------
    pd.DataFrame with:
      - track_name
      - artist
      - days_on_chart
    """
    required_cols = {"track_name", "artist", "date"}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(sorted(missing))}")

    df = df.dropna(subset=["date"]).copy()

    duration = (
        df.groupby(["track_name", "artist"])["date"]
        .nunique()
        .reset_index(name="days_on_chart")
        .sort_values("days_on_chart", ascending=False)
    )
    return duration


def compute_top_songs_by_streams(df: pd.DataFrame, n: int = 20) -> pd.DataFrame:
    """
    Compute the top N songs by total streams across all countries.

    Expects columns:
      - track_name
      - artist
      - streams

    Returns
    -------
    pd.DataFrame with:
      - track_name
      - artist
      - total_streams
    """
    required_cols = {"track_name", "artist", "streams"}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(sorted(missing))}")

    top = (
        df.groupby(["track_name", "artist"])["streams"]
        .sum()
        .reset_index(name="total_streams")
        .sort_values("total_streams", ascending=False)
        .head(n)
    )
    return top


if __name__ == "__main__":
    # Quick manual test; update to your actual file name.
    test_file = "charts_2023.csv"
    print(f"DATA_DIR = {DATA_DIR}")

    try:
        df_test = load_spotify_charts(test_file)
        print("Loaded DataFrame shape:", df_test.shape)
        print("Columns:", list(df_test.columns))
    except FileNotFoundError as exc:
        print(exc)
