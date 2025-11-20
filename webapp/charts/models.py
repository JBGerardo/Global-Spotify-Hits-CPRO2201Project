from django.db import models


class ChartEntry(models.Model):
    """
    Represents a single row from charts_2023.csv
    (one track on a chart for a given date and country).
    """

    date = models.DateField()
    country = models.CharField(max_length=100)
    position = models.IntegerField()
    streams = models.BigIntegerField()

    track_id = models.CharField(max_length=100)
    track_name = models.CharField(max_length=255)
    artist = models.CharField(max_length=255)
    artist_genres = models.TextField(blank=True)  # comma-separated or raw text
    duration = models.IntegerField(help_text="Duration in milliseconds", null=True, blank=True)
    explicit = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=["country"]),
            models.Index(fields=["track_name"]),
            models.Index(fields=["artist"]),
            models.Index(fields=["date"]),
        ]
        ordering = ["country", "date", "position"]

    def __str__(self):
        return f"{self.track_name} - {self.artist} ({self.country}, {self.date}, #{self.position})"
