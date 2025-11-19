"""
spotify_analysis.py

Core data loading & analysis functions for the
Global Spotify Hits project (CPRO 2201 - Python II).

This module will be used in:
- Jupyter notebooks (exploratory analysis)
- Django views (for showing results on the web app)
"""

from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

# Base directory: .../Global-Spotify-Hits-Python II Project/data/raw
DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"


def load_spotify_charts(csv_name: str) -> pd.DataFrame:
    """
    Load the Spotify charts CSV from the data/raw directory.

    Parameters
    ----------
    csv_name : str
        File name of the CSV (e.g., 'spotify_charts.csv').

    Returns
    -------
    pd.DataFrame
        DataFrame containing the charts data.
    """
    csv_path = DATA_DIR / csv_name
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV not found at: {csv_path}")

    df = pd.read_csv(csv_path)
    return df


def compute_country_song_counts(df: pd.DataFrame) -> pd.DataFrame:
    """
    Example analysis:
    For each song, count how many countries it appears in.

    Assumes the DataFrame includes at least:
      - 'track_name'
      - 'artist'
      - 'country'   (or 'region', depending on Kaggle schema)

    Returns
    -------
    pd.DataFrame with columns:
      - track_name
      - artist
      - country_count
    """
    required_cols = {"track_name", "artist", "country"}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(
            f"Missing required columns in DataFrame: {', '.join(sorted(missing))}"
        )

    grouped = (
        df.groupby(["track_name", "artist"])["country"]
        .nunique()
        .reset_index(name="country_count")
        .sort_values("country_count", ascending=False)
    )
    return grouped


def compute_chart_diversity_by_country(df: pd.DataFrame) -> pd.DataFrame:
    """
    Example analysis:
    For each country, calculate how many unique tracks appear.

    Returns
    -------
    pd.DataFrame with columns:
      - country
      - unique_tracks
    """
    required_cols = {"track_name", "country"}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(
            f"Missing required columns in DataFrame: {', '.join(sorted(missing))}"
        )

    diversity = (
        df.groupby("country")["track_name"]
        .nunique()
        .reset_index(name="unique_tracks")
        .sort_values("unique_tracks", ascending=False)
    )
    return diversity


def compute_average_days_on_chart(df: pd.DataFrame) -> pd.DataFrame:
    """
    Example analysis:
    Estimate how long tracks stay on the chart on average.

    Assumes DataFrame has:
      - 'track_name'
      - 'artist'
      - 'date' (convertible to datetime)

    Returns
    -------
    pd.DataFrame with columns:
      - track_name
      - artist
      - days_on_chart
    """
    required_cols = {"track_name", "artist", "date"}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(
            f"Missing required columns in DataFrame: {', '.join(sorted(missing))}"
        )

    df = df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    # Count distinct chart dates per track
    duration = (
        df.dropna(subset=["date"])
        .groupby(["track_name", "artist"])["date"]
        .nunique()
        .reset_index(name="days_on_chart")
        .sort_values("days_on_chart", ascending=False)
    )
    return duration


if __name__ == "__main__":
    # Quick manual test; update the file name once you download from Kaggle
    test_file = "YOUR_SPOTIFY_FILE.csv"  # e.g., 'charts.csv'
    print(f"DATA_DIR = {DATA_DIR}")

    try:
        df_test = load_spotify_charts(test_file)
        print("Loaded DataFrame shape:", df_test.shape)
    except FileNotFoundError as exc:
        print(exc)
