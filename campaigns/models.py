from django.db import models

from contacts.models import MediaContact


class Campaign(models.Model):
    """A PR campaign brief: the story a consultant wants covered."""

    name = models.CharField(max_length=200)
    client_name = models.CharField(max_length=200)
    brief = models.TextField(help_text="What's the news? Why does it matter? Any key facts/quotes.")
    tone = models.CharField(
        max_length=50,
        choices=[("professional", "Professional"), ("casual", "Casual"), ("bold", "Bold")],
        default="professional",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.name


class Pitch(models.Model):
    """An AI-drafted, per-contact pitch email for a campaign."""

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        SENT = "sent", "Sent"
        REPLIED = "replied", "Replied"

    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name="pitches")
    contact = models.ForeignKey(MediaContact, on_delete=models.CASCADE, related_name="pitches")
    subject = models.CharField(max_length=300, blank=True)
    body = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        unique_together = ["campaign", "contact"]

    def __str__(self) -> str:
        return f"{self.campaign.name} -> {self.contact.name}"
