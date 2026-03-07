import asyncio

import anthropic

import config

_client = anthropic.AsyncAnthropic(api_key=config.ANTHROPIC_API_KEY)

_ONE_PAGER_SYSTEM = """You are an expert academic summariser. Given source material, produce a concise study one-pager in Markdown with exactly these sections:

# <Title>

## Key Points
- 5–10 bullet points of the most important facts/ideas

## Acronyms & Definitions
- Bullet list of technical terms and their meanings (skip if none)

## Summary
2–3 paragraphs synthesising the material.

Output ONLY the Markdown — no preamble, no code fences."""

_FLOWCHART_SYSTEM = """You are a diagram expert. Given source material, produce ONLY valid Mermaid flowchart syntax (flowchart TD) showing the main concepts and their relationships.

Rules:
- Output ONLY the Mermaid code — no prose, no code fences, no backticks
- Maximum 15 nodes
- Node labels must be short (≤6 words)
- Use --> for directed edges with short edge labels where helpful
- Start with: flowchart TD"""

_TABLE_SYSTEM = """You are an expert at extracting structured knowledge. Given source material, produce a Markdown pipe table with these columns:

| Concept | Definition | Key Properties | Example |

Rules:
- 5–15 rows covering the most important concepts
- Keep each cell concise (≤20 words)
- Output ONLY the Markdown table — no preamble, no code fences"""


def _build_content(text: str, images: list) -> list:
    blocks = []
    if images:
        blocks.extend(images)
    if text:
        blocks.append({"type": "text", "text": text})
    return blocks


async def _call(system: str, content: list, max_tokens: int) -> str:
    resp = await _client.messages.create(
        model=config.MODEL,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": content}],
    )
    return resp.content[0].text.strip()


async def generate_all(text: str, images: list) -> dict:
    """Call Claude three times in parallel and return all outputs."""
    content = _build_content(text, images)

    one_pager, flowchart, table = await asyncio.gather(
        _call(_ONE_PAGER_SYSTEM, content, 2048),
        _call(_FLOWCHART_SYSTEM, content, 1024),
        _call(_TABLE_SYSTEM, content, 1024),
    )

    return {
        "one_pager": one_pager,
        "flowchart": flowchart,
        "table": table,
    }
