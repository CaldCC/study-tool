# CLAUDE.md

This file provides guidance to Claude Code when working with code in this repository.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Copy and fill in env file
cp .env.example .env   # add ANTHROPIC_API_KEY

# Run the dev server
PATH="$PATH:/Users/cordeliachuku/Library/Python/3.9/bin" uvicorn main:app --port 8000
# Then open http://localhost:8000

# Run in background (persists after shell closes)
nohup uvicorn main:app --port 8000 > /tmp/study-tool.log 2>&1 &

# Stop the server
kill $(lsof -ti :8000)

# View logs
tail -f /tmp/study-tool.log
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
GitHub: https://github.com/CaldCC/study-tool

**Never commit:** `.env` — it is in `.gitignore` and contains secrets.

## Architecture

FastAPI web app: user input → Claude AI (generate + validate + retry) → rendered output.

**Data flow:**
1. User submits URL / DOI / PDF via `static/index.html`
2. `main.py` route calls the appropriate handler in `inputs/`
3. Handler returns `{"text": str, "images": list}` — text capped at `MAX_TEXT_CHARS`
4. `processor.py` calls `claude_client.generate_all()`
5. `generate_all()` runs a generate → validate → retry loop (up to `MAX_ATTEMPTS = 3`):
   - **Attempt 1**: generates one-pager, flowchart, table in parallel via `asyncio.gather()`
   - **Validate**: all three outputs checked against the source for factual accuracy + critical gaps
   - **On warn/fail**: validation feedback injected into prompt; all three regenerated
   - **On pass** (or max attempts reached): returns final outputs + validation result
6. Frontend renders output; validation badge shown at top of output panel

**Key design details:**

### Input handlers (`inputs/`)
- `pdf_handler.py` — PyMuPDF text extraction + base64 image extraction (mirrors invoice-processor pattern)
- `url_handler.py` — httpx fetch + BeautifulSoup cleaning; PDF URLs routed to pdf_handler
- `doi_handler.py` — Crossref API metadata + Unpaywall open-access PDF fallback; falls back to abstract text

### Claude client (`claude_client.py`)
- `AsyncAnthropic` singleton client
- `MAX_ATTEMPTS = 3` — controls retry limit for the validate-and-fix loop
- **One-pager prompt**: structured Markdown with Key Points, mandatory Acronyms & Mnemonics (min 3, invent if needed), Quick Patterns, Summary
- **Flowchart prompt**: auto-detects best Mermaid diagram type from content:
  - `mindmap` → reference/categorised material (max 5 branches, 18 nodes, 3 levels)
  - `flowchart LR` → processes, cause→effect
  - `flowchart TD` → hierarchies, classifications
  - `sequenceDiagram` → actor interactions, protocols
  - `graph LR` → networks, relationship webs
- **Table prompt**: multiple colour-coded tables with standard bold emoji headings that the frontend classifier uses to apply CSS themes
- **Validation prompt**: checks one-pager + table + flowchart against source; returns JSON `{status, factual_issues, critical_gaps, summary}`

### Frontend (`static/index.html`)
- No build step — Marked.js, Mermaid.js, html2pdf.js all loaded from CDN
- **Layout**: fixed left panel (input, 380px) + right panel (output, flex)
- **Right panel states**: empty → loading spinner → output with fade-in
- **Output tabs**: One-Pager / Flow Chart / Table
- **Validation bar**: coloured badge (✅ pass / ⚠️ warn / ❌ fail) + expandable issues/gaps list; shows attempt count if >1
- **Colour-coded tables**: JS classifier reads bold emoji heading before each table and applies a CSS theme class:
  - 📊 Master Reference → Navy `#1e3a5f`
  - ⚠️ Deficiency/Signs → Red `#8b1a1a`
  - 🚨 Toxicity/Limits → Crimson `#6b1a00`
  - 💊 Interactions → Green `#1a5c35`
  - 🧠 Acronyms/Memory → Amber `#7a4500`
  - 🤰 Special Groups → Purple `#4a1a7a`
  - 🦴 Key Groupings → Teal `#1a4a5c`
- **Downloads**: all three panels have "Download PDF" buttons via html2pdf.js (flowchart → landscape A4; others → portrait A4)
- **Mermaid rendering**: uses unique ID per render (`mermaid-{timestamp}`) to prevent silent failures on re-render

### Config (`config.py`)
- Required: `ANTHROPIC_API_KEY`
- Optional: `MODEL` (default `claude-sonnet-4-6`), `MAX_TEXT_CHARS` (default `12000`)
