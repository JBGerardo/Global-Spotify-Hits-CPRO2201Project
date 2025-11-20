import math
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from charts.models import ChartEntry
from analysis.spotify_analysis import load_spotify_charts


class Command(BaseCommand):
    help = "Load Spotify chart data from CSV into the ChartEntry model."

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            type=str,
            default="charts_2023.csv",
            help="CSV file name located in data/raw (default: charts_2023.csv)",
        )
        parser.add_argument(
            "--limit",
            type=int,
            help="Optional: limit number of rows to load (for testing).",
        )

    def handle(self, *args, **options):
        csv_name = options["file"]
        limit = options.get("limit")

        # Project root = one level above 'webapp'
        project_root = Path(__file__).resolve().parents[4]
        data_dir = project_root / "data" / "raw"
        csv_path = data_dir / csv_name

        if not csv_path.exists():
            raise CommandError(f"CSV file not found at: {csv_path}")

        self.stdout.write(self.style.NOTICE(f"Loading data from: {csv_path}"))

        # Use our existing loader, which normalizes column names
        df = load_spotify_charts(csv_name)

        if limit is not None:
            df = df.head(limit)

        # Sanity check: we expect these columns AFTER renaming
        required_cols = [
            "date",
            "country",
            "position",
            "streams",
            "track_id",
            "track_name",
            "artist",
            "artist_genres",
            "duration",
            "explicit",
        ]
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            raise CommandError(f"Missing required columns in DataFrame: {missing}")

        # Optional: clear existing data first (ok for now, makes reruns easy)
        ChartEntry.objects.all().delete()
        self.stdout.write(self.style.WARNING("Existing ChartEntry rows deleted."))

        rows_to_create = []

        # Iterate over DataFrame rows
        for row in df.itertuples(index=False):
            try:
                # date: ensure it's a plain 'YYYY-MM-DD' string
                date_val = getattr(row, "date")
                date_str = str(date_val).split(" ")[0] if date_val is not None else None

                # explicit: robust bool conversion
                explicit_val = getattr(row, "explicit")
                if isinstance(explicit_val, str):
                    explicit_val = explicit_val.strip().lower() in ("1", "true", "yes")
                else:
                    explicit_val = bool(explicit_val)

                # duration: may be NaN or None
                duration_val = getattr(row, "duration", None)
                if duration_val is not None and isinstance(duration_val, float) and math.isnan(
                    duration_val
                ):
                    duration_val = None

                entry = ChartEntry(
                    date=date_str,
                    country=getattr(row, "country"),
                    position=int(getattr(row, "position")),
                    streams=int(getattr(row, "streams")),
                    track_id=getattr(row, "track_id"),
                    track_name=getattr(row, "track_name"),
                    artist=getattr(row, "artist"),
                    artist_genres=getattr(row, "artist_genres", "") or "",
                    duration=duration_val,
                    explicit=explicit_val,
                )
                rows_to_create.append(entry)

            except Exception as exc:
                self.stderr.write(f"Skipping row due to error: {exc}")
                continue

        if not rows_to_create:
            self.stdout.write(self.style.WARNING("No rows to create."))
            return

        self.stdout.write(f"Creating {len(rows_to_create)} ChartEntry rows...")
        with transaction.atomic():
            ChartEntry.objects.bulk_create(rows_to_create, batch_size=1000)

        self.stdout.write(self.style.SUCCESS(f"Finished loading {len(rows_to_create)} rows."))
