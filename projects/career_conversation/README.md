# Career Conversation

AI career assistant for **Harsha Melur Nagesh** — answers questions about background, skills, and experience using your resume and summary.

**Live demo:** https://huggingface.co/spaces/harshamelurnagesh/career_conversations2

## Setup

```bash
cd projects/career_conversation
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

Create `.env` in this folder (or use the parent `agents/.env`):

```
OPENAI_API_KEY=sk-...
PUSHOVER_USER=...
PUSHOVER_TOKEN=...
```

## Run locally

```bash
python app.py
```

## Deploy to Hugging Face

```bash
gradio deploy --title career_conversations2 --app-file app.py --provider spaces
```

## Files

- `app.py` — Gradio chat app
- `me/Harsha_Resume.pdf` — resume context
- `me/summary.txt` — short bio context
