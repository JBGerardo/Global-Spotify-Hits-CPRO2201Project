from django.db import models


class ChartEntry(models.Model):
    """
    ChartEntry model

    This model represents a single row from the charts_2023.csv file:
    - one track
    - on one chart date
    - in one country

    Each instance is therefore a combination of:
    (date, country, position, track information, artist information).
    """

    # Basic chart information
    date = models.DateField()
    country = models.CharField(
        max_length=100,
        help_text="Country code or name from the original dataset (for example: 'us', 'global').",
    )
    position = models.IntegerField(
        help_text="Chart position of the track on that date (1 = top position)."
    )
    streams = models.BigIntegerField(
        help_text="Number of streams for this track on that date."
    )

    # Track information (unique ID and readable name)
    track_id = models.CharField(
        max_length=100,
        help_text="Spotify track identifier from the CSV file.",
    )
    track_name = models.CharField(
        max_length=255,
        help_text="Human-readable track name.",
    )

    # Artist information
    artist = models.CharField(
        max_length=255,
        help_text="Primary artist name for this track.",
    )
    artist_genres = models.TextField(
        blank=True,
        help_text="Optional: genres for the artist, often comma-separated or raw text.",
    )

    # Extra metadata about the track
    duration = models.IntegerField(
        help_text="Duration in milliseconds.",
        null=True,
        blank=True,
    )
    explicit = models.BooleanField(
        default=False,
        help_text="Whether the track is marked as explicit in the dataset.",
    )

    class Meta:
        """
        Meta configuration for ChartEntry.

        - indexes: speed up common queries by country, track_name, artist and date.
        - ordering: default ordering when we call ChartEntry.objects.all().
        """

        indexes = [
            models.Index(fields=["country"]),
            models.Index(fields=["track_name"]),
            models.Index(fields=["artist"]),
            models.Index(fields=["date"]),
        ]
        ordering = ["country", "date", "position"]

    def __str__(self) -> str:
        """
        String representation used in Django admin and shell.

        Example:
            "Song Title - Artist Name (us, 2023-01-01, #1)"
        """
        return f"{self.track_name} - {self.artist} ({self.country}, {self.date}, #{self.position})"
