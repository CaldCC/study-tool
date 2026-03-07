import asyncio

import anthropic

import config

_client = anthropic.AsyncAnthropic(api_key=config.ANTHROPIC_API_KEY)

_ONE_PAGER_SYSTEM = """You are an expert academic summariser producing structured study notes.

Given source material, produce a study one-pager in Markdown following this exact structure:

# 📚 <Title>

## 🔑 Key Points
- 5–10 bullet points of the most important facts/ideas

## 🧠 Memory Acronyms & Mnemonics
Create or extract useful acronyms/mnemonics to remember key concepts. Format each as:
**"ACRONYM"** = What each letter stands for
- Brief explanation of why it helps

If no acronyms exist in the source, invent useful ones. Always include at least 2–3.

## ⚡ Quick Patterns to Know
- Important relationships, rules of thumb, or patterns worth remembering
- Drug/interaction pairs, absorption rules, groupings, etc. (adapt to subject matter)

## 📋 Summary
2–3 paragraphs synthesising the material.

Output ONLY the Markdown — no preamble, no code fences."""

_FLOWCHART_SYSTEM = """You are a diagram expert. Given source material, produce ONLY valid Mermaid flowchart syntax (flowchart TD) showing the main concepts and their relationships.

Rules:
- Output ONLY the Mermaid code — no prose, no code fences, no backticks
- Maximum 15 nodes
- Node labels must be short (≤6 words)
- Use --> for directed edges with short edge labels where helpful
- Start with: flowchart TD"""

_TABLE_SYSTEM = """You are an expert at extracting structured knowledge into study tables.

Given source material, produce multiple focused Markdown tables, each preceded by a bold emoji heading. Model your output on this style:

**📊 Master Reference Table**
| Nutrient/Concept | Daily Dose / Value | Key Functions | Best Sources |
|---|---|---|---|
| ... | ... | ... | ... |

**⚠️ Deficiency Signs**
| Nutrient/Concept | Key Signs / Symptoms |
|---|---|
| ... | ... |

**🚨 Toxicity / Upper Limits** (include only if relevant)
| Nutrient/Concept | Safe Upper Level | Toxicity Signs |
|---|---|---|
| ... | ... | ... |

**💊 Key Interactions** (include only if relevant)
| Item | Interacts With | Clinical Note |
|---|---|---|
| ... | ... | ... |

Rules:
- Adapt column names and table types to the subject matter — use whichever tables make sense
- Always include at least a master reference table and a deficiency/key-signs table
- Keep cells concise (≤20 words)
- Include acronyms as a row or note where relevant
- Output ONLY the Markdown tables with their headings — no other prose, no code fences"""


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
        _call(_TABLE_SYSTEM, content, 2048),
    )

    return {
        "one_pager": one_pager,
        "flowchart": flowchart,
        "table": table,
    }
