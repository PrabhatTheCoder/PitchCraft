"""AI generation logic, isolated from views/tasks so it's mockable in tests
without needing a real API call or a Celery worker running.

Provider is chosen via settings.AI_PROVIDER ("groq" | "anthropic") --
swapping providers means adding one function + one dict entry, not a new
class hierarchy.
"""
import json

from django.conf import settings

from contacts.models import MediaContact

from campaigns.models import Campaign

SYSTEM_PROMPT = (
    "You are a senior PR consultant writing a short, personalized media pitch email. "
    "Write like a human who has actually read the journalist's beat, not a mail-merge template. "
    "Keep it under 150 words. Never use placeholders like [Your Name] or [Company] -- "
    "always use the actual sender name and details provided to you. "
    "Respond ONLY with JSON: "
    '{"subject": "...", "body": "..."}. No markdown, no commentary, no code fences.'
)


class PitchGenerationError(Exception):
    """Raised on any AI-call failure so callers (the Celery task) can retry
    or mark the Pitch failed without leaking provider-specific exceptions."""



def build_user_prompt(campaign: Campaign, contact: MediaContact) -> str:
    sender_name = campaign.user.get_full_name() or campaign.user.username

    return (
        f"Campaign: {campaign.name}\n"
        f"Client: {campaign.client_name}\n"
        f"Tone: {campaign.get_tone_display()}\n"
        f"Brief:\n{campaign.brief}\n\n"
        f"Journalist: {contact.name}, {contact.outlet}\n"
        f"Beat: {contact.beat or 'unspecified'}\n"
        f"Notes on this journalist: {contact.notes or 'none'}\n\n"
        f"Sender name (sign the email as this person, no placeholder): {sender_name}\n\n"
        "Write a subject line and a short pitch email body addressed to this journalist, "
        "connecting the campaign brief to their specific beat/interests."
    )


def _call_groq(prompt: str) -> str:
    if not settings.GROQ_API_KEY:
        raise PitchGenerationError(
            "GROQ_API_KEY is not set. Add it to your .env file (see .env.example)."
        )

    from groq import Groq  # lazy import — module loads fine even if groq isn't installed

    client = Groq(api_key=settings.GROQ_API_KEY)

    schema = {
        "type": "object",
        "properties": {
            "subject": {"type": "string"},
            "body": {"type": "string"},
        },
        "required": ["subject", "body"],
        "additionalProperties": False,
    }

    def _attempt(extra_instruction: str = "") -> str:
        response = client.chat.completions.create(
            model=settings.GROQ_MODEL,
            max_tokens=500,
            response_format={
                "type": "json_schema",
                "json_schema": {"name": "pitch", "strict": True, "schema": schema},
            },
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt + extra_instruction},
            ],
        )
        return response.choices[0].message.content.strip()

    try:
        return _attempt()
    except Exception:
        # json_schema/strict mode is documented as "never invalid" only on
        # select models -- one retry with a blunter instruction recovers
        # most transient empty/malformed generations before we give up and
        # let the Celery task's own retry(exc=...) take over.
        try:
            return _attempt(
                "\n\nReturn ONLY the JSON object with keys 'subject' and 'body'. No other text."
            )
        except Exception as exc:
            raise PitchGenerationError(f"Groq API call failed: {exc}") from exc


def _call_anthropic(prompt: str) -> str:
    if not settings.ANTHROPIC_API_KEY:
        raise PitchGenerationError(
            "ANTHROPIC_API_KEY is not set. Add it to your .env file (see .env.example)."
        )

    import anthropic  # lazy import — module loads fine even if anthropic isn't installed

    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    try:
        response = client.messages.create(
            model=settings.ANTHROPIC_MODEL,
            max_tokens=500,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
    except Exception as exc:
        raise PitchGenerationError(f"Anthropic API call failed: {exc}") from exc

    return "".join(block.text for block in response.content if block.type == "text").strip()


# Add a new provider by writing one _call_x(prompt) -> str function and
# registering it here — generate_pitch() and every caller stay unchanged.
_PROVIDERS = {
    "groq": _call_groq,
    "anthropic": _call_anthropic,
}


def generate_pitch(campaign: Campaign, contact: MediaContact) -> dict:
    """Call the configured AI provider and return {'subject': str, 'body': str}."""
    provider = getattr(settings, "AI_PROVIDER", "groq")

    try:
        call = _PROVIDERS[provider]
    except KeyError:
        raise PitchGenerationError(
            f"Unknown AI_PROVIDER '{provider}'. Choose one of: {', '.join(_PROVIDERS)}."
        )

    text = call(build_user_prompt(campaign, contact))

    try:
        data = json.loads(text)
        subject = data["subject"]
        body = data["body"]
    except (json.JSONDecodeError, KeyError) as exc:
        raise PitchGenerationError(f"Model returned unparseable output: {text[:200]}") from exc

    return {"subject": subject, "body": body}