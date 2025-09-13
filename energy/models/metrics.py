from django.db import models

from .base import BaseTimestampModel

# from django.utils import timezone


class TopicMetrics(BaseTimestampModel):
    """Metriche per topic MQTT"""

    topic = models.CharField(max_length=255, db_index=True)
    device = models.ForeignKey(
        "DeviceConfiguration", on_delete=models.CASCADE, related_name="topic_metrics"
    )
    messages_count = models.IntegerField(default=0)
    errors_count = models.IntegerField(default=0)
    avg_processing_time = models.FloatField(default=0)  # in millisecondi
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()
    period_type = models.CharField(
        max_length=10,
        choices=[
            ("HOUR", "Hourly"),
            ("DAY", "Daily"),
            ("MONTH", "Monthly"),
            ("YEAR", "Yearly"),
        ],
    )

    class Meta:
        unique_together = ["topic", "period_start", "period_type"]
        indexes = [
            models.Index(fields=["period_type", "period_start"]),
            models.Index(fields=["device", "period_type"]),
        ]
