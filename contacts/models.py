from django.db import models


class MediaContact(models.Model):
    """A journalist / editor / influencer a PR consultant might pitch."""

    name = models.CharField(max_length=200)
    email = models.EmailField(unique=True)
    outlet = models.CharField(max_length=200, help_text="Publication or channel, e.g. TechCrunch")
    beat = models.CharField(max_length=200, blank=True, help_text="Topic focus, e.g. fintech, climate tech")
    notes = models.TextField(blank=True, help_text="Style, past coverage, preferences")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return f"{self.name} ({self.outlet})"
