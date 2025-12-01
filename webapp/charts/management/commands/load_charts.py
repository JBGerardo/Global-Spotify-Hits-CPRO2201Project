"""
Custom Django management command to load Spotify charts data into the database.

Usage examples:

    python manage.py load_charts
    python manage.py load_charts --file charts_2023.csv
    python manage.py load_charts --file charts_2023.csv --limit 1000

This command:

1. Uses the existing load_spotify_charts function to read the CSV file
   and normalise column names.
2. Optionally limits the number of rows for testing.
3. Deletes existing ChartEntry rows (so reruns are easy during development).
4. Iterates over the DataFrame and creates ChartEntry objects.
5. Uses bulk_create inside a transaction for better performance.
"""

import math
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from charts.models import ChartEntry
from analysis.spotify_analysis import load_spotify_charts


class Command(BaseCommand):
    """
    Django management command class.

    """

    help = "Load Spotify chart data from CSV into the ChartEntry model."

    def add_arguments(self, parser):
        """
        Define command-line arguments.

        --limit:
            If provided, we only load the first N rows
            from the CSV. This is mainly for quick testing.
        """
        parser.add_argument(
            "--file",
            type=str,
            default="charts_2023.csv",
            help="CSV file name located in data/raw (default: charts_2023.csv).",
        )
        parser.add_argument(
            "--limit",
            type=int,
            help="Optional: limit number of rows to load (for testing).",
        )

    def handle(self, *args, **options):
        """
        Main entry point when the command is run.

        We:
        - Read options from the command line.
        - Ask load_spotify_charts to load and clean the CSV into a DataFrame.
        - Check that required columns exist.
        - Delete existing ChartEntry rows.
        - Convert each DataFrame row into a ChartEntry object.
        - Bulk insert all new rows in one transaction.
        """
        csv_name = options["file"]
        limit = options.get("limit")

        try:
            df = load_spotify_charts(csv_name)
        except FileNotFoundError as exc:
            # CommandError makes Django show the message and exit with a
            # non-zero status code.
            raise CommandError(str(exc)) from exc

        # If a limit is given, take only the first N rows.
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

        # We clear existing data so that rerunning the command replaces it
        # with a fresh copy from the CSV.
        self.stdout.write(self.style.WARNING("Deleting existing ChartEntry rows..."))
        ChartEntry.objects.all().delete()

        rows_to_create = []

        # Iterate over each row of the DataFrame.
        #
        # itertuples is a simple way to loop over rows and access columns
        # as attributes:
        #   for row in df.itertuples(index=False):
        #       row.track_name, row.country, row.streams, ...
        for row in df.itertuples(index=False):
            try:
                # date: convert to a plain 'YYYY-MM-DD' string
                date_val = getattr(row, "date")
                if date_val is not None:
                    # If the date has a time part, we keep only the date part.
                    date_str = str(date_val).split(" ")[0]
                else:
                    date_str = None

                # explicit: robust conversion to a boolean value.
                explicit_val = getattr(row, "explicit")
                if isinstance(explicit_val, str):
                    explicit_val = explicit_val.strip().lower() in ("1", "true", "yes")
                else:
                    explicit_val = bool(explicit_val)

                # duration: may be NaN or None. We convert NaN to None.
                duration_val = getattr(row, "duration", None)
                if isinstance(duration_val, float) and math.isnan(duration_val):
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
                # If anything goes wrong for a single row (for example,
                # bad date format), we skip it and continue. We also log
                # the error to stderr so it is visible in the console.
                self.stderr.write(f"Skipping row due to error: {exc}")
                continue

        if not rows_to_create:
            self.stdout.write(self.style.WARNING("No rows to create."))
            return

        # Bulk insert all rows in a single transaction. If anything fails,
        # the transaction is rolled back and no partial data is written.
        self.stdout.write(f"Creating {len(rows_to_create)} ChartEntry rows...")
        with transaction.atomic():
            ChartEntry.objects.bulk_create(rows_to_create, batch_size=1000)

        self.stdout.write(
            self.style.SUCCESS(f"Finished loading {len(rows_to_create)} rows.")
        )
