import asyncio

import anthropic

import config

_client = anthropic.AsyncAnthropic(api_key=config.ANTHROPIC_API_KEY)

_ONE_PAGER_SYSTEM = """You are an expert academic summariser producing structured study notes.

Given source material, produce a study one-pager in Markdown following this EXACT structure:

# 📚 <Title>

## 🔑 Key Points
- 5–10 bullet points of the most important facts/ideas

## 🧠 Memory Acronyms & Mnemonics
THIS SECTION IS MANDATORY — always produce at least 3 entries.
- Extract any acronyms already present in the source (e.g. ADEK, RICE, SMART)
- For key concept groups not already abbreviated, INVENT a memorable acronym
- Format EVERY entry exactly like this:

**"ADEK"** = **A**ntioxidant · **D**ensity · **E**lectrolytes · **K**inase
→ Fat-soluble vitamins stored in liver/fat — toxicity risk if excess

**"SICK"** = **S**poon nails · **I**nfections · **C**racked mouth · **K**—fatigue
→ Signs of iron deficiency anaemia

Invent new acronyms for any important list of 3+ items that lacks one.
Always explain what each letter stands for AND why the grouping matters.

## ⚡ Quick Patterns & Rules
- Key relationships, rules of thumb, pairings, and groupings worth memorising
- e.g. absorption conflicts, dose thresholds, category rules

## 📋 Summary
2–3 paragraphs synthesising the material.

Output ONLY the Markdown — no preamble, no code fences."""

_FLOWCHART_SYSTEM = """You are a diagram expert. Given source material, first assess the content type, then choose the BEST Mermaid diagram type from the list below and produce ONLY valid Mermaid syntax for it.

DIAGRAM SELECTION RULES — pick exactly one:

1. mindmap
   Use when: reference material, categorised lists, topics that radiate from a central theme
   Example content: vitamins, taxonomies, concept overviews, study notes
   Syntax starts with: mindmap

2. flowchart LR
   Use when: processes, pipelines, decision trees, cause → effect chains
   Example content: how something works step by step, if/else logic, workflows
   Syntax starts with: flowchart LR

3. flowchart TD
   Use when: hierarchies, parent → child relationships, classification trees
   Example content: organisational structures, inheritance, ranked categories
   Syntax starts with: flowchart TD

4. sequenceDiagram
   Use when: interactions between actors over time, protocols, request/response cycles
   Example content: API flows, biological signalling, communication patterns
   Syntax starts with: sequenceDiagram

5. graph LR
   Use when: networks of relationships without a clear direction or hierarchy
   Example content: interconnected systems, dependency maps, relationship webs
   Syntax starts with: graph LR

OUTPUT RULES — apply regardless of which diagram type you choose:
- Output ONLY the Mermaid code — no prose, no explanation, no code fences, no backticks
- Keep all labels short (≤6 words)
- Maximum 15 nodes / participants
- Always choose the type that makes the content easiest to understand at a glance"""

_TABLE_SYSTEM = """You are an expert at extracting structured knowledge into colour-coded study tables.

Produce multiple focused Markdown tables. ALWAYS begin each table with a bold emoji heading on its own line — the heading keyword controls the colour the app applies, so use these EXACT heading keywords:

**📊 Master Reference Table** — main overview (columns vary by subject)
**⚠️ Deficiency Signs** — signs, symptoms, or failure modes
**🚨 Toxicity & Upper Limits** — risks, overdose, safety thresholds
**💊 Key Interactions** — drug/element/system interactions, pairings, conflicts
**🧠 Acronyms & Memory Aids** — every acronym from the source + invented ones for key groups
**🤰 Special Groups** — pregnancy, children, elderly, life-stage notes (if relevant)
**🦴 Key Groupings** — thematic clusters, bundles, related concept sets (if relevant)

Rules:
- ALWAYS include: Master Reference Table, Deficiency Signs, Acronyms & Memory Aids
- Include other tables only when the source contains relevant data
- Keep cells concise (≤20 words)
- For the Acronyms table use columns: | Acronym | Stands For | Meaning / Use |
- Output ONLY the Markdown tables with their bold headings — no other prose, no code fences

Example Acronyms table:
**🧠 Acronyms & Memory Aids**
| Acronym | Stands For | Meaning / Use |
|---|---|---|
| ADEK | A, D, E, K | Fat-soluble vitamins — stored in liver, toxicity risk |
| SICK | Spoon nails · Infections · Cracked mouth · K-fatigue | Signs of iron deficiency |"""


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
