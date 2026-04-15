# MR Digest

A self-hosted daily email digest for [Marginal Revolution](https://marginalrevolution.com). Runs as a cron job, fetches new posts via RSS, extracts a formatted excerpt from each one, and mails you a clean HTML digest.

## How it works

1. **State tracking** — a small JSON file records when the last digest was sent. On the first run, only posts from the current day are included; after that, only posts newer than the last run.
2. **RSS fetch** — new posts are pulled from the MR feed (`marginalrevolution.com/feed`).
3. **Excerpt extraction** — each post's HTML is fetched, boilerplate is stripped, and up to ~1000 characters of formatted content (preserving paragraphs, blockquotes, lists) is extracted.
4. **Digest rendering** — excerpts and links are rendered into an HTML email via a Jinja2 template.
5. **Email delivery** — the digest is sent via Gmail SMTP using an [App Password](https://support.google.com/accounts/answer/185833).

## Requirements

- Python 3.10+
- A Gmail account with 2-Step Verification enabled (for the App Password)
- The `claude` CLI installed and authenticated (used by `run.sh` to activate the correct environment — no API calls are made to Claude)

## Setup

```bash
git clone <repo-url>
cd mr-digest
bash setup.sh
```

`setup.sh` will:
- Create a Python virtual environment and install dependencies
- Copy `.env.example` to `.env` if it doesn't exist yet
- Install a cron job that runs the digest daily at 4:00 PM local time

Then edit `.env` with your credentials:

```
GMAIL_USER=sender@gmail.com
GMAIL_APP_PASSWORD=xxxx_xxxx_xxxx_xxxx
DIGEST_TO_EMAIL=recipient@example.com
```

**Getting a Gmail App Password:**
1. Go to [myaccount.google.com](https://myaccount.google.com) → Security
2. Enable 2-Step Verification (required)
3. Search for "App passwords", create one named "MR Digest"
4. Paste the 16-character password into `GMAIL_APP_PASSWORD`

## Manual run

```bash
bash run.sh
tail -f logs/digest.log
```

## Files

```
digest.py          — fetches posts, extracts excerpts, builds the digest
mailer.py          — sends the digest via Gmail SMTP
templates/
  digest.html      — Jinja2 HTML email template
run.sh             — cron wrapper (activates venv, runs digest, logs output)
setup.sh           — one-time setup script
requirements.txt   — Python dependencies
.env.example       — template for required environment variables
```

## Configuration

All configuration lives in `.env` (never committed):

| Variable | Description |
|---|---|
| `GMAIL_USER` | Gmail address used as the sender |
| `GMAIL_APP_PASSWORD` | 16-character Gmail App Password |
| `DIGEST_TO_EMAIL` | Address where the digest is delivered |

The cron schedule (`0 16 * * *`) and excerpt length (1000 characters) can be adjusted in `setup.sh` and `digest.py` respectively.
