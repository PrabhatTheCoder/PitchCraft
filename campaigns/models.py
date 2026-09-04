import uuid

from django.db import models
from django.utils import timezone

from contacts.models import MediaContact


class Campaign(models.Model):
    """A PR campaign brief: the story a consultant wants covered."""

    class Tone(models.TextChoices):
        PROFESSIONAL = "professional", "Professional"
        CASUAL = "casual", "Casual"
        BOLD = "bold", "Bold"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False,)
    user = models.ForeignKey('users.User', on_delete=models.CASCADE,related_name="campaigns",)
    name = models.CharField(max_length=200)
    client_name = models.CharField(max_length=200)
    brief = models.TextField(help_text="What's the news? Why does it matter? Any key facts/quotes.")
    tone = models.CharField(max_length=20, choices=Tone.choices, default=Tone.PROFESSIONAL)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["client_name"])]

    def __str__(self) -> str:
        return self.name


class Pitch(models.Model):
    """An AI-drafted, per-contact pitch email for a campaign.

    Generation runs in a Celery task (Claude call is slow + can fail
    transiently), so `generation_status` tracks the task's progress
    separately from `status`, which tracks the *outreach* lifecycle
    (draft -> sent -> replied) once content exists.
    """

    class GenerationStatus(models.TextChoices):
        PENDING = "pending", "Pending"          # row created, task not yet run
        GENERATING = "generating", "Generating"  # task picked it up
        READY = "ready", "Ready"                 # subject/body populated
        FAILED = "failed", "Failed"              # task raised; see generation_error

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        SENT = "sent", "Sent"
        REPLIED = "replied", "Replied"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    

    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name="pitches")
    contact = models.ForeignKey(MediaContact, on_delete=models.CASCADE, related_name="pitches")

    subject = models.CharField(max_length=300, blank=True)
    body = models.TextField(blank=True)

    generation_status = models.CharField(
        max_length=12, choices=GenerationStatus.choices,
        default=GenerationStatus.PENDING, db_index=True,
    )
    generation_error = models.TextField(blank=True)
    generation_retry_count = models.PositiveSmallIntegerField(default=0)
    generated_at = models.DateTimeField(null=True, blank=True)

    status = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            # one pitch per campaign+contact — re-generating updates this row,
            # never duplicates it
            models.UniqueConstraint(fields=["campaign", "contact"], name="unique_pitch_per_campaign_contact"),
            # a READY pitch must actually have content
            models.CheckConstraint(
                condition=(
                    models.Q(generation_status="ready", subject__gt="", body__gt="")
                    | ~models.Q(generation_status="ready")
                ),
                name="ready_pitch_has_content",
            ),
        ]
        indexes = [
            models.Index(fields=["campaign", "status"]),
            models.Index(fields=["contact", "generation_status"]),
        ]

    def __str__(self) -> str:
        return f"{self.campaign.name} -> {self.contact.name}"

    def mark_generating(self) -> None:
        self.generation_status = self.GenerationStatus.GENERATING
        self.save(update_fields=["generation_status", "updated_at"])

    def mark_ready(self, subject: str, body: str) -> None:
        self.subject = subject
        self.body = body
        self.generation_status = self.GenerationStatus.READY
        self.generation_error = ""
        self.generated_at = timezone.now()
        self.save(update_fields=[
            "subject", "body", "generation_status",
            "generation_error", "generated_at", "updated_at",
        ])

    def mark_failed(self, error: str) -> None:
        self.generation_status = self.GenerationStatus.FAILED
        self.generation_error = error[:2000]
        self.generation_retry_count += 1
        self.save(update_fields=["generation_status", "generation_error", "generation_retry_count", "updated_at"])

    def mark_sent(self) -> None:
        self.status = self.Status.SENT
        self.save(update_fields=["status", "updated_at"])