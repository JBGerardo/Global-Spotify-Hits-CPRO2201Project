from pathlib import Path

import pandas as pd
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from charts.models import ChartEntry


class Command(BaseCommand):
    """
    Load Spotify chart data from CSV into the ChartEntry table.

<<<<<<< HEAD
    Usage examples:
        python manage.py load_charts --reset
        python manage.py load_charts --file charts_2023.csv --limit 5000 --reset
        python manage.py load_charts --file charts_2023.csv
=======
>>>>>>> 06ba461f5812338f4ecefba887a22e90ebc4dc40
    """

    help = "Load Spotify chart data from data/raw/*.csv into the ChartEntry table."

    def add_arguments(self, parser):
<<<<<<< HEAD
=======
        """
        Define command-line arguments.

        --limit:
            If provided, we only load the first N rows
            from the CSV. This is mainly for quick testing.
        """
>>>>>>> 06ba461f5812338f4ecefba887a22e90ebc4dc40
        parser.add_argument(
            "--file",
            default="charts_2023.csv",
            help="CSV filename inside data/raw/ (default: charts_2023.csv)",
        )
        parser.add_argument(
            "--limit",
            type=int,
            help="Optional limit on the number of rows to load (for testing).",
        )
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete existing ChartEntry rows before loading.",
        )

    def handle(self, *args, **options):
        filename = options["file"]
        limit = options.get("limit")
        reset = options.get("reset", False)

<<<<<<< HEAD
        # data/ folder is one level above the Django project (webapp/)
        base_dir = Path(settings.BASE_DIR).parent
        csv_path = base_dir / "data" / "raw" / filename

        if not csv_path.exists():
            raise CommandError(f"CSV file not found at: {csv_path}")

        self.stdout.write(self.style.NOTICE(f"Loading data from {csv_path}"))

        # Load CSV with pandas
=======
>>>>>>> 06ba461f5812338f4ecefba887a22e90ebc4dc40
        try:
            df = pd.read_csv(csv_path)
        except Exception as exc:
            raise CommandError(f"Failed to read CSV: {exc}") from exc

        # Limit rows if requested
        if limit is not None:
            df = df.head(limit)

        # --- Normalize column names and map aliases ---
        # make everything lower-case for easier matching
        df.columns = [c.strip().lower() for c in df.columns]

        # Some datasets use "region" instead of "country"
        if "country" not in df.columns and "region" in df.columns:
            df = df.rename(columns={"region": "country"})

        # Some datasets use "name" instead of "track_name"
        if "track_name" not in df.columns:
            if "name" in df.columns:
                df = df.rename(columns={"name": "track_name"})
            elif "track" in df.columns:
                df = df.rename(columns={"track": "track_name"})

        # Some datasets use "artists" instead of "artist"
        if "artist" not in df.columns:
            if "artists" in df.columns:
                df = df.rename(columns={"artists": "artist"})
            elif "artist_name" in df.columns:
                df = df.rename(columns={"artist_name": "artist"})

        # Some datasets use "id" for the track ID
        if "track_id" not in df.columns and "id" in df.columns:
            df = df.rename(columns={"id": "track_id"})

        # Required columns for our model (after renaming)
        required_columns = {
            "date",
            "country",
            "position",
            "streams",
            "track_id",
            "track_name",
            "artist",
        }

        missing = required_columns - set(df.columns)
        if missing:
            raise CommandError(
                f"CSV file is missing required columns even after mapping: {sorted(missing)}"
            )

<<<<<<< HEAD
        # Convert date column
        df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date
=======
        # We clear existing data so that rerunning the command replaces it
        # with a fresh copy from the CSV.
        self.stdout.write(self.style.WARNING("Deleting existing ChartEntry rows..."))
        ChartEntry.objects.all().delete()
>>>>>>> 06ba461f5812338f4ecefba887a22e90ebc4dc40

        # Optional columns
        if "artist_genres" not in df.columns:
            df["artist_genres"] = ""
        if "duration" not in df.columns:
            df["duration"] = pd.NA
        if "explicit" not in df.columns:
            df["explicit"] = False

        # Optionally clear existing data
        if reset:
            self.stdout.write(self.style.WARNING("Deleting existing ChartEntry rows..."))
            ChartEntry.objects.all().delete()

        entries: list[ChartEntry] = []

        for row in df.itertuples(index=False):
            # basic validation
            if pd.isna(row.date) or pd.isna(row.country) or pd.isna(row.position):
                continue

            # position
            try:
                position = int(row.position)
            except (TypeError, ValueError):
                continue

            # streams (fallback to 0 if bad)
            try:
                streams = int(getattr(row, "streams", 0) or 0)
            except (TypeError, ValueError):
                streams = 0

            # duration (optional)
            duration_val = getattr(row, "duration", None)
            duration = None
            if pd.notna(duration_val):
                try:
                    duration = int(duration_val)
                except (TypeError, ValueError):
                    duration = None

            # explicit flag
            explicit_val = getattr(row, "explicit", False)
            explicit = bool(explicit_val)

            entries.append(
                ChartEntry(
                    date=row.date,
                    country=str(row.country).lower(),
                    position=position,
                    streams=streams,
                    track_id=row.track_id,
                    track_name=row.track_name,
                    artist=row.artist,
                    artist_genres=getattr(row, "artist_genres", "") or "",
                    duration=duration,
                    explicit=explicit,
                )
            )

        if not entries:
            self.stdout.write(self.style.WARNING("No valid rows found to insert."))
            return

        self.stdout.write(
            self.style.NOTICE(f"Creating {len(entries)} ChartEntry rows in bulk...")
        )
        ChartEntry.objects.bulk_create(entries, batch_size=5000)

        self.stdout.write(self.style.SUCCESS("Finished loading chart data."))
