# PitchCraft

A small Django + DRF API for PR consultants: keep a media contact list, define a
campaign brief, and generate a personalized pitch email per journalist using
Claude — instead of one generic mail-merge blast.

## Why this idea

PR firms don't need a bigger CRM, they need less generic outreach. Most pitch
tools either (a) store contacts with no AI, or (b) generate one pitch and blast
it to everyone. PitchCraft ties a campaign brief to *each contact's* beat and
notes, so the generated pitch is actually addressed to what that journalist
covers.

## Data model

- `MediaContact` — name, email, outlet, beat, freeform notes.
- `Campaign` — the story: client, brief, tone.
- `Pitch` — one campaign x one contact = one AI-drafted subject/body,
  with a status (`draft` / `sent` / `replied`). Unique per
  (campaign, contact) so re-generating updates the same row instead of
  duplicating it.

## API

| Method | Endpoint                          | Purpose                          |
|--------|------------------------------------|-----------------------------------|
| CRUD   | `/api/contacts/`                   | Manage media contacts             |
| CRUD   | `/api/campaigns/`                  | Manage campaign briefs            |
| GET    | `/api/pitches/`                    | List generated pitches            |
| POST   | `/api/pitches/generate/`           | `{campaign_id, contact_id}` → calls Claude, upserts a `Pitch` |
| POST   | `/api/pitches/{id}/mark_sent/`     | Mark a pitch as sent               |

`/api/contacts/?search=fintech` searches name/outlet/beat.

The AI call lives in `campaigns/services.py`, separate from the view, so it's
mockable in tests and swappable for a different provider later.

## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env   # then add your ANTHROPIC_API_KEY

python manage.py migrate
python manage.py createsuperuser   # optional, for /admin/
python manage.py runserver
```

Run tests:

```bash
python manage.py test
```

## How this was built with AI

This was built with an AI coding assistant (Claude) directing implementation
from a spec, not autocomplete-as-you-type:

1. **Spec first.** Decided the model shape (Contact / Campaign / Pitch) and
   the one interesting endpoint (`generate`) before writing code — the spec
   above is close to what was written as the actual prompt.
2. **AI wrote the Django boilerplate** — models, serializers, viewsets,
   routers, admin registration — from that spec.
3. **The AI-integration boundary was deliberately isolated**
   (`campaigns/services.py`) so it could be unit-tested without hitting the
   real Anthropic API — `test_generate_pitch_*` in `campaigns/tests.py` mock
   `generate_pitch` and assert on status codes, idempotency (re-generating
   updates the same `Pitch` row instead of duplicating), and failure handling
   (a `PitchGenerationError` surfaces as a `502`, not a `500`).
4. **Verification**: read every generated file, ran `python manage.py test`,
   and manually exercised `/api/pitches/generate/` against the real Anthropic
   API with a sample contact/campaign to confirm the JSON contract
   (`{"subject": ..., "body": ...}`) actually holds up against real model
   output, not just the mocked tests.

## What I'd do next

- Swap the JSON-via-prompt contract for Claude's structured tool-use /
  JSON schema output instead of asking nicely for JSON in the prompt.
- Add a `/pitches/{id}/regenerate-with-feedback/` endpoint so a consultant
  can say "shorter" or "less formal" and get a revision instead of a full
  redo.
- Bulk generate: one campaign → pitches for a whole contact list, with
  rate-limit-aware batching.
- Auth (this is currently open — fine for a take-home, not for prod).
