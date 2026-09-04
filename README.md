# PitchCraft

🌐 **Live Demo:** http://54.179.240.41/

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

## Async task processing
 
- **Celery** — runs pitch generation (the AI call) off the request thread
- **Redis** — Celery broker + result backend
- Retry-on-failure built into the task (`max_retries=3`, 30s backoff) for transient AI/network errors

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

cp .env.example .env   # then add your Groq_API_KEY

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
   real Groq API — `test_generate_pitch_*` in `campaigns/tests.py` mock
   `generate_pitch` and assert on status codes, idempotency (re-generating
   updates the same `Pitch` row instead of duplicating), and failure handling
   (a `PitchGenerationError` surfaces as a `502`, not a `500`).

## Example usage
 
**1. Sign up**
```
POST /api/v1/auth/signup/
{ "email": "priya@acmepr.com", "password": "..." }
→ { "access": "...", "refresh": "..." }
```
 
**2. Add a media contact**
```
POST /api/v1/contacts/create-media-contacts/
{ "name": "Fatima Al Rashid", "email": "fatima@gulfbusinessnews.com",
  "outlet": "Gulf Business News", "beat": "fintech, startups",
  "notes": "Prefers short, data-driven pitches." }
```
 
**3. Add a campaign brief**
```
POST /api/v1/campaigns/create-campaigns/
{ "name": "Acme Pay Series A", "client_name": "Acme Pay",
  "brief": "Acme Pay, a Dubai-based B2B payments startup, closed an $8M Series A. Expanding into Saudi Arabia next quarter.",
  "tone": "professional" }
```
 
**4. Generate a pitch** — enqueues a Celery task, returns immediately
```
POST /api/v1/campaigns/pitches/
{ "campaign": "<campaign-id>", "contact": "<contact-id>" }
→ { "generation_status": "generating", ... }
```
 
**5. Poll until ready** (frontend does this every 4s)
```
GET /api/v1/campaigns/pitches/
→ { "generation_status": "ready",
    "subject": "Dubai fintech Acme Pay raises $8M, eyes Saudi expansion",
    "body": "Hi Fatima, given your recent piece on UAE fintech funding...",
    "status": "draft" }
```
 
**6. Mark it sent** once the consultant has copied it into their own email client
```
PATCH /api/v1/campaigns/pitches/<id>/
{ "status": "sent" }
```

## What I'd do next
 
### Product features
 
- **RAG pipeline for pitch generation** — let clients upload multiple reference docs (past coverage, brand guidelines, bios) and use retrieval to ground the AI-generated pitch in that context, producing stronger, more on-brand output.
- **Multi-channel outreach** — extend beyond the current channel with WhatsApp API, Email, SMS, and Voice, drawing on prior experience integrating these.
- **In-app email sending** — let clients send the generated pitch as an email directly from the page, without copy-pasting into a separate client.
- **Cron-based email automation** — let clients schedule and automate recurring sends (e.g., follow-ups) instead of triggering everything manually.
