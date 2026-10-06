"""
Turns drift results + normalized transaction data into the audit report:
plain-English narrative sections mapped to what CBN Circular
BSD/DIR/PUB/LAB/019/002 and NITDA's AI-law documentation actually ask for.

Generates all sections in a single call, not one call per section - five
independent calls repeated the same PSI numbers and conclusion in every
section. Performance metrics and evidence-sufficiency are computed in
evidence.py, in plain Python, before the LLM ever sees them - the LLM
explains what the numbers mean, it does not decide what they are.

Sections come back as plain text separated by markers, not JSON. Asking
an LLM to wrap long free-text paragraphs inside strict JSON is fragile -
one stray unescaped quote inside a sentence breaks the whole parse. A
delimiter the model just has to copy exactly is far more reliable than
asking it to produce syntactically perfect JSON around prose every time.

v1 deliberately omits a bias/fairness section - computing real fairness
metrics needs protected-attribute data, which NDPA restricts. Sequence
drift + performance first; bias is a carefully-scoped later phase.
"""
import json
import re
from llm_client import call_llm
from evidence import performance_metrics, model_health

SECTION_KEYS = [
    "system_overview",
    "data_and_inputs",
    "drift_summary",
    "performance_summary",
    "decision_logic_summary",
]

MARKER = "###{key}###"


def _parse_sections(raw: str) -> dict:
    """Split the model's delimited output into a dict, tolerant of extra
    whitespace or stray commentary the model adds outside the markers."""
    sections = {}
    for i, key in enumerate(SECTION_KEYS):
        start_marker = MARKER.format(key=key.upper())
        start = raw.find(start_marker)
        if start == -1:
            sections[key] = ""
            continue
        start += len(start_marker)
        if i + 1 < len(SECTION_KEYS):
            next_marker = MARKER.format(key=SECTION_KEYS[i + 1].upper())
            end = raw.find(next_marker, start)
            end = end if end != -1 else len(raw)
        else:
            end = len(raw)
        sections[key] = raw[start:end].strip()
    return sections


async def generate_full_report(drift_results: dict, normalized_rows: list[dict]) -> dict:
    perf = performance_metrics(normalized_rows)
    health = model_health(drift_results["overall_status"], perf["status"])

    section_markers = "\n".join(MARKER.format(key=k.upper()) for k in SECTION_KEYS)

    prompt = f"""You are writing a compliance audit report for a Nigerian
financial institution's AI system, to satisfy CBN Circular
BSD/DIR/PUB/LAB/019/002 and NITDA's AI documentation requirements.

Write for a compliance officer with no ML background who will hand this
directly to an examiner. Be specific and factual - no marketing language.

Drift analysis results (already computed, do not recalculate):
{json.dumps(drift_results, indent=2)}

Performance metrics (already computed, do not recalculate or contradict
this - if status is "insufficient" or "limited", say plainly that
performance cannot be reliably assessed, do not substitute other numbers
for it):
{json.dumps(perf, indent=2)}

Overall model health (already determined, do not recalculate): {health}

Sample of the underlying data (first 5 rows):
{json.dumps(normalized_rows[:5], indent=2, default=str)}

Write five sections with DIFFERENT focuses - do not restate the same PSI
numbers and the same "retrain the model" conclusion in every section:
- system_overview: what the system does, and the headline drift finding only.
- data_and_inputs: what data it uses and the audit trail it keeps - not a
  repeat of the drift numbers.
- drift_summary: the only section that should walk through the per-feature
  PSI numbers in detail.
- performance_summary: report the precision/recall/f1 values given above if
  status allows it, or state plainly that evidence is insufficient/limited
  if that's the given status - never invent a number the data above doesn't
  provide.
- decision_logic_summary: how inputs become a decision, illustrated with
  one concrete example from the sample data - not a repeat of the others.

Format your entire response EXACTLY like this, with each marker on its own
line, copied exactly as shown, followed by that section's plain-text
paragraphs (2-4 short paragraphs, no markdown, no bullet points):

{section_markers}

Write nothing before the first marker and nothing after the last section."""

    raw = await call_llm(prompt, max_tokens=3000)
    sections = _parse_sections(raw)

    return {
        "sections": sections,
        "drift_results": drift_results,
        "performance": perf,
        "model_health": health,
        "bias_section": "Not included in v1 - see README for why fairness metrics are deferred to a later phase.",
        "row_count_analyzed": len(normalized_rows),
        "normalized_rows": normalized_rows,
    }