"""AI generation logic, isolated from views so it's easy to test and swap providers."""
from __future__ import annotations

import json

from django.conf import settings

from contacts.models import MediaContact

from .models import Campaign

SYSTEM_PROMPT = (
    "You are a senior PR consultant writing a short, personalized media pitch email. "
    "Write like a human who has actually read the journalist's beat, not a mail-merge template. "
    "Keep it under 150 words. Respond ONLY with JSON: "
    '{"subject": "...", "body": "..."}. No markdown, no commentary, no code fences.'
)


class PitchGenerationError(Exception):
    """Raised when the AI call fails or returns something unusable."""


def build_user_prompt(campaign: Campaign, contact: MediaContact) -> str:
    return (
        f"Campaign: {campaign.name}\n"
        f"Client: {campaign.client_name}\n"
        f"Tone: {campaign.get_tone_display()}\n"
        f"Brief:\n{campaign.brief}\n\n"
        f"Journalist: {contact.name}, {contact.outlet}\n"
        f"Beat: {contact.beat or 'unspecified'}\n"
        f"Notes on this journalist: {contact.notes or 'none'}\n\n"
        "Write a subject line and a short pitch email body addressed to this journalist, "
        "connecting the campaign brief to their specific beat/interests."
    )


def generate_pitch(campaign: Campaign, contact: MediaContact) -> dict:
    """Call the Anthropic API and return {'subject': str, 'body': str}.

    Raises PitchGenerationError on any failure so callers can decide how to
    surface it (this keeps the Django view free of provider-specific errors).
    """
    if not settings.ANTHROPIC_API_KEY:
        raise PitchGenerationError(
            "ANTHROPIC_API_KEY is not set. Add it to your .env file (see .env.example)."
        )

    import anthropic  # imported lazily so tests can run without the package configured

    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    try:
        response = client.messages.create(
            model=settings.ANTHROPIC_MODEL,
            max_tokens=500,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": build_user_prompt(campaign, contact)}],
        )
    except Exception as exc:  # noqa: BLE001 - surface as a domain error
        raise PitchGenerationError(f"Anthropic API call failed: {exc}") from exc

    text = "".join(block.text for block in response.content if block.type == "text").strip()

    try:
        data = json.loads(text)
        subject = data["subject"]
        body = data["body"]
    except (json.JSONDecodeError, KeyError) as exc:
        raise PitchGenerationError(f"Model returned unparseable output: {text[:200]}") from exc

    return {"subject": subject, "body": body}
