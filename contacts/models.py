from django.db import models
import uuid

class MediaContact(models.Model):
    """A journalist / editor / influencer a PR consultant might pitch."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('users.user', on_delete=models.CASCADE, related_name="media_contacts",)
    name = models.CharField(max_length=200)
    email = models.EmailField(unique=True)
    outlet = models.CharField(max_length=200, help_text="Publication or channel, e.g. TechCrunch")
    beat = models.CharField(max_length=200, blank=True, help_text="Topic focus, e.g. fintech, climate tech")
    notes = models.TextField(blank=True, help_text="Style, past coverage, preferences")

    is_active = models.BooleanField(
        default=True,
        help_text="Unsubscribed/bounced contacts stay for history but drop out of pitch generation.",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["outlet"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.outlet})"