"""
spotify_analysis.py

Core data loading & analysis functions for the
Global Spotify Hits project.

This will be used both in notebooks and eventually
by the Django views.
"""

import pandas as pd
import numpy as np
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"


def load_spotify_charts(csv_name: str) -> pd.DataFrame:
    """
    Load the Spotify charts CSV from the data/raw directory.
    """
    csv_path = DATA_DIR / csv_name
    return pd.read_csv(csv_path)


if __name__ == "__main__":
    # Quick manual test (update with your actual file name later)
    print("Analysis module ready. Place your CSV in data/raw and call load_spotify_charts().")
