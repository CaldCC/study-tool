import httpx
from bs4 import BeautifulSoup

import config
from inputs import pdf_handler


async def extract(url: str) -> dict:
    """Fetch a URL and return cleaned text.

    If the URL points to a PDF, delegates to pdf_handler.
    Returns {"text": str, "images": list}.
    """
    async with httpx.AsyncClient(follow_redirects=True, timeout=15.0) as client:
        response = await client.get(url, headers={"User-Agent": "study-tool/1.0"})
        response.raise_for_status()

    content_type = response.headers.get("content-type", "")
    if url.lower().endswith(".pdf") or "application/pdf" in content_type:
        return pdf_handler.extract(response.content)

    soup = BeautifulSoup(response.text, "html.parser")

    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()

    text = soup.get_text(separator="\n", strip=True)
    # Collapse excessive blank lines
    lines = [ln for ln in text.splitlines() if ln.strip()]
    cleaned = "\n".join(lines)

    return {
        "text": cleaned[: config.MAX_TEXT_CHARS],
        "images": [],
    }
