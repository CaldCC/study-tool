# CLAUDE.md

This file provides guidance to Claude Code when working with code in this repository.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Copy and fill in env file
cp .env.example .env   # add ANTHROPIC_API_KEY

# Run the dev server
uvicorn main:app --reload --port 8000
# Then open http://localhost:8000
```

There is no test suite. Validate changes by running the server and testing each input type (URL, DOI, PDF) manually.

## Git Workflow

**After every change, commit and push to GitHub:**

```bash
git add <changed files>
git commit -m "short description of change"
git push
```

Never leave changes uncommitted. The GitHub repo is the source of truth for all code state.

**Never commit:** `.env` — it is in `.gitignore` and contains secrets.

## Architecture

Single-run FastAPI web app that pipelines user input → Claude AI → rendered output.

**Data flow:**
1. User submits a URL / DOI / PDF via `static/index.html`
2. `main.py` route receives the request and calls the appropriate handler in `inputs/`
3. Handler returns `{"text": str, "images": list}` — text capped at `MAX_TEXT_CHARS`
4. `processor.py` calls `claude_client.generate_all()` which fires three Claude calls in parallel
5. Results (`one_pager`, `flowchart`, `table`) are returned as JSON
6. Frontend renders Markdown with Marked.js and Mermaid diagrams with Mermaid.js

**Key design details:**
- `inputs/pdf_handler.py` — PyMuPDF text + base64 image extraction (mirrors invoice-processor/extractor.py)
- `inputs/url_handler.py` — httpx fetch + BeautifulSoup cleaning; PDF URLs are routed to pdf_handler
- `inputs/doi_handler.py` — Crossref metadata + optional Unpaywall open-access PDF; falls back to abstract text
- `claude_client.py` — three async Claude calls via `asyncio.gather()`; uses `AsyncAnthropic`
- `config.py` — `.env` loading; required: `ANTHROPIC_API_KEY`; optional: `MODEL`, `MAX_TEXT_CHARS`
- Frontend is a single `static/index.html` with no build step; Mermaid/Marked loaded from CDN
