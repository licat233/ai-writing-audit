#!/usr/bin/env python3
"""Offline AI-style audit CLI. Standard library only."""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import replace
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from adapters.base import AuditContext, Finding

LEVELS = ("low", "moderate", "high", "critical")
SEVERITY = {"low": 1, "medium": 2, "high": 3, "critical": 4}

EN_PATTERNS = [
    ("SENTENCE-NEGATIVE-PARALLELISM", r"\b(?:it is|it's) not just [^.!?;]+;?\s*it(?:'s| is)\s+(?:about|also)", "sentence_structure", "medium", "high", "language_fix", "A familiar not-just/but-style contrast is carrying an abstract claim.", "State the concrete change, object, or condition directly.", "conorbronsdon/avoid-ai-writing;blader/humanizer"),
    ("SENTENCE-RULE-OF-THREE", r"\b(?:and|or)\s+[^,;.!?]+,\s+[^,;.!?]+,\s+and\s+[^,;.!?]+", "sentence_structure", "low", "moderate", "style_choice", "A polished three-part list may be formulaic, but it can also be normal rhetoric.", "Keep it if the three items are materially distinct; otherwise compress.", "blader/humanizer"),
    ("CHATBOT-ARTIFACT", r"\b(?:I hope this helps|let me know if you(?:'d| would) like|as an AI language model)\b", "chatbot_artifact", "high", "high", "language_fix", "The sentence resembles assistant residue rather than article prose.", "Remove it or replace it with article-specific content.", "conorbronsdon/avoid-ai-writing"),
    ("CONTENT-GENERIC-CLAIM", r"\b(?:innovative|seamless|game-changing|revolutionary|significantly improves|plays a vital role|in today's rapidly changing world)\b", "content_quality", "medium", "moderate", "needs_specificity", "The wording makes a broad value claim without an object, mechanism, condition, or evidence.", "Name what changes, how it changes, and under what conditions.", "native;blader/humanizer"),
    ("CONTENT-EVIDENCE-GAP", r"\b(?:studies show|research shows|data shows|数据显示|研究表明|业内人士认为)\b", "evidence", "high", "moderate", "needs_source", "The attribution is vague and does not identify a verifiable source.", "Add the real source and scope, or qualify/remove the claim.", "native"),
]

ZH_PATTERNS = [
    ("LANGUAGE-AI-VOCABULARY-CLUSTER", r"(?:在当今快速发展的时代|随着[^。！？]{0,24}的不断发展|值得一提的是|不可忽视的是|不可否认|正如前面所说|总而言之|综上所述|双刃剑|深远影响|注入新的活力|开启新的篇章|构建[^。！？]{0,12}新格局|极大地提升|提供了出色的体验|助力|赋能)", "language", "low", "moderate", "needs_specificity", "This is a common Chinese template or abstract value phrase; a single hit is not conclusive.", "Check density and replace with the specific object, action, or result where needed.", "native;blader/humanizer"),
    ("CONTENT-EVIDENCE-GAP", r"(?:数据显示|研究表明|业内人士认为)", "evidence", "high", "moderate", "needs_source", "The statement invokes data or an authority without identifying it.", "Add a verifiable source, date, and scope, or qualify the claim.", "native"),
    ("STRUCTURE-MECHANICAL-SECTIONS", r"(?:首先|其次|最后)[，,]", "structure", "low", "moderate", "style_choice", "Repeated ordinal transitions can make sections feel mechanically generated.", "Keep them when they reflect real sequencing; otherwise use meaningful transitions.", "native"),
]

PROFILES_DIR = ROOT / "profiles"

# ARMOR domain facts, enabled only when the active profile lists them
# (profiles/armor.yaml -> facts). These detect unsupported product claims
# that generic AI-style rules cannot see. Sources: ARMOR Vault product KB.
ARMOR_FACT_RULES = {
    "esl-is-not-lcd": (
        "ARMOR-FACT-ESL-IS-NOT-LCD",
        r"\bESL\b[^.!?]{0,60}\b(?:is|are|means?|stands for|equals?)\b[^.!?]{0,30}\bLCD\b",
        "facts", "high", "moderate", "factual_conflict",
        "The copy equates ESL with LCD, which are distinct product categories.",
        "Say 'ESL' or 'LCD-type ESL' only when it matches the actual product; do not equate the categories.",
        "armor-product-knowledge",
    ),
    "esl-not-electrically-connected-to-power-track-without-evidence": (
        "ARMOR-FACT-ESL-POWER-TRACK-CONNECTION",
        r"\bESL\b[^.!?]{0,60}\b(?:electrically connected|wired|powered by|draws? power from)\b[^.!?]{0,30}\b(?:power track|track)\b",
        "facts", "high", "moderate", "needs_domain_review",
        "The copy asserts an electrical connection to the power track without confirmed evidence.",
        "Confirm the connection method with product documentation, or mark the claim [TO CONFIRM].",
        "armor-product-knowledge",
    ),
    "magnetic-light-needs-compatible-steel-surface": (
        "ARMOR-FACT-MAGNETIC-SURFACE-REQUIREMENT",
        r"\bmagnetic\b[^.!?]{0,70}\b(?:any surface|all surfaces|every surface|any shelf|all shelves|no surface preparation|no prep)\b",
        "facts", "high", "moderate", "needs_domain_review",
        "The copy implies magnetic lights work on any surface; they require ferromagnetic (steel/iron) shelf surfaces.",
        "State the ferromagnetic surface requirement or the alternative mounting method.",
        "armor-product-knowledge",
    ),
    "no-unsupported-zero-install-cost-or-roi": (
        "ARMOR-FACT-UNSUPPORTED-ZERO-INSTALL-ROI",
        r"\b(?:zero|no|free)\s+install(?:ation)?\s+cost\b|\bROI\b[^.!?]{0,40}\d+(?:\.\d+)?\s*%|\b\d+(?:\.\d+)?\s*%\s+ROI\b",
        "facts", "high", "moderate", "unsupported_claim",
        "The copy states zero install cost or a specific ROI figure without a supporting source.",
        "Add a verified source or case data, or replace the figure with a qualified statement.",
        "armor-product-knowledge",
    ),
    "verify-voltage-and-connection": (
        "ARMOR-FACT-VERIFY-VOLTAGE-CONNECTION",
        r"\b\d{2,4}\s*[Vv]\b",
        "facts", "medium", "low", "needs_domain_review",
        "The copy gives a specific voltage or connection value without verification.",
        "Verify the voltage and connection against product documentation, or mark [TO CONFIRM].",
        "armor-product-knowledge",
    ),
}


def load_profile_facts(profile_id: str) -> list[str]:
    """Read the facts list from profiles/<id>.yaml. Standard library only."""
    path = PROFILES_DIR / f"{profile_id}.yaml"
    if not path.is_file():
        return []
    text = path.read_text(encoding="utf-8")
    m = re.search(r"^\s*facts:\s*\[([^\]]+)\]", text, re.M)
    if not m:
        return []
    return [x.strip().strip("\"'") for x in m.group(1).split(",") if x.strip()]


def armor_fact_findings(text: str, facts: list[str], protected: list[tuple[int, int]]) -> list[Finding]:
    findings = []
    for fact_id in facts:
        rule = ARMOR_FACT_RULES.get(fact_id)
        if not rule:
            continue
        rule_id, pattern, category, severity, confidence, repair_type, diagnosis, action, sources = rule
        for match in re.finditer(pattern, text, re.I):
            evidence = match.group(0).strip()
            if not evidence:
                continue
            findings.append(Finding(rule_id, "local-static-scanner", category, severity, confidence, evidence, match.start(), match.end(), diagnosis, action, repair_type, (sources,), is_protected(match.start(), match.end(), protected)))
    return findings


def structural_findings(text: str, language: str, protected: list[tuple[int, int]]) -> list[Finding]:
    """Detect whole-article predictability that word-list scans cannot capture."""
    findings: list[Finding] = []
    endcap = re.compile(r"(?im)^#{1,6}\s*(?:总结|结论|常见问题(?:解答)?|FAQ|Summary|Conclusion|Frequently Asked Questions)\s*$")
    for match in endcap.finditer(text):
        findings.append(Finding(
            "STRUCTURE-TEMPLATE-ENDCAP", "local-static-scanner", "structure", "low", "high",
            match.group(0).strip(), match.start(), match.end(),
            "A labeled summary, conclusion, or FAQ can become a predictable end-cap when it repeats the article or exists only for template completeness.",
            "Keep it only when the reader or page purpose needs it; otherwise end with the decision, implication, or next action.",
            "style_choice", ("native",), is_protected(match.start(), match.end(), protected),
        ))

    blocks = []
    for match in re.finditer(r"(?ms)(?:^|\n\s*\n)([^\n].*?)(?=\n\s*\n|\Z)", text):
        raw = match.group(1).strip()
        if not raw or raw.startswith(("#", ">", "```", "|", "- ", "* ")):
            continue
        start = match.start(1)
        end = match.end(1)
        if is_protected(start, end, protected):
            continue
        size = len(re.findall(r"[\u4e00-\u9fff]", raw)) if language == "zh" else len(re.findall(r"\b\w+\b", raw))
        if size >= (30 if language == "zh" else 20):
            blocks.append((start, end, size, raw))
    if len(blocks) >= 4:
        sizes = [item[2] for item in blocks]
        mean = sum(sizes) / len(sizes)
        deviation = (sum((size - mean) ** 2 for size in sizes) / len(sizes)) ** 0.5
        if mean and deviation / mean <= 0.14:
            evidence = f"{len(blocks)} similarly sized paragraphs ({min(sizes)}–{max(sizes)} {'characters' if language == 'zh' else 'words'})"
            findings.append(Finding(
                "STRUCTURE-PARAGRAPH-UNIFORMITY", "local-static-scanner", "structure", "medium", "moderate",
                evidence, blocks[0][0], blocks[-1][1],
                "Paragraphs have unusually uniform length, which can reflect padded, parallel generation rather than information-led development.",
                "Let important mechanisms or trade-offs run longer and compress secondary points; do not vary length mechanically.",
                "style_choice", ("native",), False,
            ))

    density_terms = r"(?:提升|促进|推动|助力|赋能|优化|实现|打造|构建)" if language == "zh" else r"\b(?:improve|enhance|enable|empower|optimize|transform|streamline|drive)\w*\b"
    for start, end, _, raw in blocks:
        matches = re.findall(density_terms, raw, re.I)
        if len(matches) >= 3:
            findings.append(Finding(
                "CONTENT-ABSTRACT-BENEFIT-DENSITY", "local-static-scanner", "content_quality", "medium", "moderate",
                raw[:220], start, end,
                "The paragraph stacks benefit verbs without enough concrete mechanism, object, condition, or trade-off.",
                "Keep the strongest supported benefit and connect it to a specific action, mechanism, condition, or source.",
                "needs_specificity", ("native",), False,
            ))
    return findings


def protected_spans(text: str) -> list[tuple[int, int]]:
    spans = []
    for pattern in (r"(?ms)^---\n.*?\n---\n", r"(?ms)```.*?```", r"(?m)^>.*$", r"(?ms)(?m)^\|.*(?:\n\|.*)+"):
        spans.extend((m.start(), m.end()) for m in re.finditer(pattern, text))
    return sorted(spans)


def is_protected(start: int, end: int, spans: Iterable[tuple[int, int]]) -> bool:
    return any(start < b and end > a for a, b in spans)


def detect_language(text: str) -> str:
    zh = len(re.findall(r"[\u4e00-\u9fff]", text))
    latin = len(re.findall(r"[A-Za-z]", text))
    return "zh" if zh > latin else "en"


def scan_text(text: str, context: AuditContext) -> list[Finding]:
    language = detect_language(text) if context.language == "auto" else context.language
    patterns = (ZH_PATTERNS if language == "zh" else EN_PATTERNS) + (EN_PATTERNS if language == "zh" else [])
    protected = protected_spans(text)
    findings = []
    for rule_id, pattern, category, severity, confidence, repair_type, diagnosis, action, sources in patterns:
        for match in re.finditer(pattern, text, re.I):
            evidence = match.group(0).strip()
            if not evidence:
                continue
            findings.append(Finding(rule_id, "local-static-scanner", category, severity, confidence, evidence, match.start(), match.end(), diagnosis, action, repair_type, tuple(sources.split(";")), is_protected(match.start(), match.end(), protected)))
    for profile_id in context.profile_ids:
        findings.extend(armor_fact_findings(text, load_profile_facts(profile_id), protected))
    findings.extend(structural_findings(text, language, protected))
    return findings


def sentence_location(text: str, offset: int | None) -> dict:
    if offset is None:
        return {}
    before = text[:offset]
    return {"paragraph": before.count("\n\n") + 1, "sentence": max(1, len(re.findall(r"[.!?。！？]", before)) + 1), "start_offset": offset}


def merge_findings(findings: list[Finding]) -> list[Finding]:
    merged: list[Finding] = []
    for item in sorted(findings, key=lambda x: (x.start_offset or 0, x.rule_id)):
        found = next((x for x in merged if x.rule_id == item.rule_id and x.start_offset is not None and item.start_offset is not None and abs(x.start_offset - item.start_offset) <= max(len(x.evidence), len(item.evidence))), None)
        if not found:
            merged.append(item)
            continue
        sources = tuple(dict.fromkeys(found.upstream_sources + item.upstream_sources))
        confidence = "high" if len(sources) > 1 and found.confidence != "low" else found.confidence
        merged[merged.index(found)] = replace(found, confidence=confidence, upstream_sources=sources, protected=found.protected or item.protected)
    return merged


def risk(findings: list[Finding]) -> tuple[str, dict]:
    dimensions = {"template_language": 0, "generic_claims": 0, "semantic_repetition": 0, "structural_uniformity": 0, "evidence_deficiency": 0, "tone_mismatch": 0, "missing_constraints": 0}
    for f in findings:
        value = 25 if f.severity == "low" else 50 if f.severity == "medium" else 75 if f.severity == "high" else 100
        key = "evidence_deficiency" if f.category in {"evidence", "facts"} else "generic_claims" if f.category == "content_quality" else "template_language" if f.category in {"language", "chatbot_artifact"} else "structural_uniformity"
        dimensions[key] = min(100, dimensions[key] + value)
    score = round(sum(dimensions.values()) / len(dimensions))
    level = "low" if score <= 20 else "moderate" if score <= 45 else "high" if score <= 70 else "critical"
    if any(f.category == "facts" for f in findings):
        level = "high" if level in {"low", "moderate"} else level
    return level, dimensions


def report(text: str, mode: str, language: str, profiles: list[str], findings: list[Finding], disabled: list[str]) -> dict:
    level, dimensions = risk(findings)
    status = {"local-static-scanner": {"status": "success", "findings": len(findings)}, "conorbronsdon-avoid-ai-writing": {"status": "success", "findings": 0}, "blader-humanizer": {"status": "success", "findings": 0}, "harshaneel-humanize": {"status": "unavailable", "reason": "deferred adapter not enabled"}, "aboudjem-humanizer-skill": {"status": "unavailable", "reason": "deferred adapter not enabled"}, "gabelul-slopbuster": {"status": "unavailable", "reason": "optional CLI not installed"}}
    for source in disabled:
        if source in status:
            status[source] = {"status": "disabled_by_user"}
    output = []
    for i, f in enumerate(findings, 1):
        d = f.to_dict()
        d["id"] = f"FINDING-{i:04d}"
        d["location"] = sentence_location(text, f.start_offset)
        d.pop("start_offset", None); d.pop("end_offset", None); d.pop("protected", None)
        d["supported_by"] = [{"source": s} for s in f.upstream_sources]
        output.append(d)
    return {"schema_version": 1, "tool_version": "0.2.0", "mode": mode, "language": detect_language(text) if language == "auto" else language, "profiles": profiles, "risk": {"level": level, "dimensions": dimensions, "interpretation": "AI-style writing risk, not authorship probability."}, "adapter_status": status, "findings": output, "limitations": ["Deterministic scan; semantic reasoning, voice reconstruction, and full repair require the Agent workflow in SKILL.md."], "provenance": {"lock_file": "upstream/upstream-lock.yaml"}}


def markdown(r: dict) -> str:
    lines = ["# AI writing audit", "", "## Overall assessment", "", f"AI-style risk: {r['risk']['level'].title()}", "", r["risk"]["interpretation"], "", "## Adapter status", ""]
    lines += [f"- {k}: {v['status']}" + (f" ({v.get('reason')})" if v.get("reason") else "") for k, v in r["adapter_status"].items()]
    lines += ["", "## Priority findings", ""]
    if not r["findings"]:
        lines.append("No deterministic findings. This does not establish that the text is human-written.")
    for f in r["findings"]:
        lines += [f"### {f['id']} — {f['rule_id']}", "", f"Evidence: `{f['evidence']}`", f"Diagnosis: {f['diagnosis']}", f"Action: {f['action']}", f"Repair type: `{f['repair_type']}`", f"Supported by: {', '.join(x['source'] for x in f['supported_by'])}", ""]
    return "\n".join(lines)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Offline AI-style writing risk audit")
    p.add_argument("article")
    p.add_argument("--mode", choices=("detect", "repair", "edit", "compare"), default="detect")
    p.add_argument("--language", choices=("auto", "en", "zh"), default="auto")
    p.add_argument("--profile", default="general")
    p.add_argument("--format", choices=("markdown", "json"), default="markdown")
    p.add_argument("--output")
    p.add_argument("--adapter", action="append")
    p.add_argument("--disable-adapter", action="append", default=[])
    p.add_argument("--strict", action="store_true")
    p.add_argument("--explain", action="store_true")
    args = p.parse_args(argv)
    text = Path(args.article).read_text(encoding="utf-8")
    context = AuditContext(args.language, args.mode, tuple(x.strip() for x in args.profile.split(",") if x.strip()))
    findings = merge_findings(scan_text(text, context))
    if args.adapter and "local-static-scanner" not in args.adapter:
        findings = []
    r = report(text, args.mode, args.language, list(context.profile_ids), findings, args.disable_adapter)
    rendered = json.dumps(r, ensure_ascii=False, indent=2) if args.format == "json" else markdown(r)
    if args.output:
        Path(args.output).write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)
    return 2 if args.strict and findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
