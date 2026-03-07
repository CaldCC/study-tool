import re

import httpx

import config
from inputs import pdf_handler

_DOI_RE = re.compile(r"^10\.\d{4,}/\S+$")
_CROSSREF = "https://api.crossref.org/works/{doi}"
_UNPAYWALL = "https://api.unpaywall.org/v2/{doi}?email=study-tool@local"


def _validate(doi: str) -> str:
    doi = doi.strip()
    # Strip common URL prefixes
    doi = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", doi)
    if not _DOI_RE.match(doi):
        raise ValueError(f"Invalid DOI: {doi!r}")
    return doi


async def extract(doi: str) -> dict:
    """Fetch metadata + optional PDF for a DOI.

    Returns {"text": str, "images": list}.
    """
    doi = _validate(doi)

    async with httpx.AsyncClient(follow_redirects=True, timeout=15.0) as client:
        # 1. Crossref metadata
        meta_resp = await client.get(
            _CROSSREF.format(doi=doi),
            headers={"User-Agent": "study-tool/1.0 (mailto:study-tool@local)"},
        )
        meta_resp.raise_for_status()
        work = meta_resp.json().get("message", {})

        title = " / ".join(work.get("title", ["Unknown title"]))
        abstract = work.get("abstract", "")
        # Strip JATS XML tags sometimes present in Crossref abstracts
        abstract = re.sub(r"<[^>]+>", "", abstract)
        authors = [
            f"{a.get('given', '')} {a.get('family', '')}".strip()
            for a in work.get("author", [])
        ]
        year = (work.get("published", {}).get("date-parts") or [[None]])[0][0]
        journal = (work.get("container-title") or [""])[0]

        # 2. Try Unpaywall for open-access PDF
        try:
            uw_resp = await client.get(
                _UNPAYWALL.format(doi=doi),
                headers={"User-Agent": "study-tool/1.0"},
            )
            uw_resp.raise_for_status()
            uw_data = uw_resp.json()
            pdf_url = None
            best = uw_data.get("best_oa_location") or {}
            pdf_url = best.get("url_for_pdf")

            if pdf_url:
                pdf_resp = await client.get(pdf_url)
                pdf_resp.raise_for_status()
                return pdf_handler.extract(pdf_resp.content)
        except Exception:
            pass

    # Fallback: construct text from metadata
    meta_text = (
        f"Title: {title}\n"
        f"Authors: {', '.join(authors) or 'Unknown'}\n"
        f"Year: {year or 'Unknown'}\n"
        f"Journal: {journal or 'Unknown'}\n"
        f"DOI: {doi}\n\n"
        f"Abstract:\n{abstract}"
    )
    return {
        "text": meta_text[: config.MAX_TEXT_CHARS],
        "images": [],
    }
