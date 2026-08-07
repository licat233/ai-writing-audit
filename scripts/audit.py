#!/usr/bin/env python3
"""Offline, reproducible AI-style editorial-risk scanner.

This CLI detects deterministic signals only. Full repair is intentionally an
agent-led workflow defined by SKILL.md and references/native-optimization.md.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from adapters.base import AuditContext, Finding


TOOL_VERSION = "0.3.0"
SEVERITY_VALUE = {"low": 25, "medium": 50, "high": 75, "critical": 100}
DIMENSIONS = (
    "template_language",
    "generic_claims",
    "semantic_repetition",
    "structural_uniformity",
    "evidence_deficiency",
    "tone_mismatch",
    "missing_constraints",
)
PROFILES_DIR = ROOT / "profiles"
NATIVE_RULES = ROOT / "rules" / "native" / "voice-optimization.yaml"


EN_PATTERNS = [
    ("SENTENCE-NEGATIVE-PARALLELISM", r"\b(?:it is|it's) not just [^.!?;]+;?\s*it(?:'s| is)\s+(?:about|also)", "sentence_structure", "medium", "high", "language_fix", "A familiar not-just/but-style contrast is carrying an abstract claim.", "State the concrete change, object, or condition directly.", "conorbronsdon/avoid-ai-writing;blader/humanizer"),
    ("SENTENCE-RULE-OF-THREE", r"\b(?:and|or)\s+[^,;.!?]+,\s+[^,;.!?]+,\s+and\s+[^,;.!?]+", "sentence_structure", "low", "moderate", "style_choice", "A polished three-part list may be formulaic, but it can also be normal rhetoric.", "Keep it only when the three items are materially distinct.", "blader/humanizer"),
    ("CHATBOT-ARTIFACT", r"\b(?:I hope this helps|let me know if you(?:'d| would) like|as an AI language model)\b", "chatbot_artifact", "high", "high", "language_fix", "The sentence resembles assistant residue rather than article prose.", "Remove it or replace it with article-specific content.", "conorbronsdon/avoid-ai-writing"),
    ("CONTENT-GENERIC-CLAIM", r"\b(?:innovative|seamless|game-changing|revolutionary|significantly improves|plays a vital role|in today's rapidly changing world)\b", "content_quality", "medium", "moderate", "needs_specificity", "The wording makes a broad value claim without a mechanism, condition, or evidence.", "Name what changes, how it changes, and under what conditions.", "native;blader/humanizer"),
    ("CONTENT-EVIDENCE-GAP", r"\b(?:studies show|research shows|data shows)\b", "evidence", "high", "moderate", "needs_source", "The attribution is vague and does not identify a verifiable source.", "Add the real source and scope, or qualify/remove the claim.", "native"),
]

ZH_PATTERNS = [
    ("LANGUAGE-AI-VOCABULARY-CLUSTER", r"(?:在当今快速发展的时代|随着[^。！？]{0,24}的不断发展|值得一提的是|不可忽视的是|不可否认|正如前面所说|总而言之|综上所述|双刃剑|深远影响|注入新的活力|开启新的篇章|构建[^。！？]{0,12}新格局|极大地提升|提供了出色的体验|助力|赋能)", "language", "low", "moderate", "needs_specificity", "This is a common Chinese template or abstract value phrase; a single hit is not conclusive.", "Replace it with the specific object, action, result, or limitation where evidence permits.", "native;blader/humanizer"),
    ("CONTENT-EVIDENCE-GAP", r"(?:数据显示|研究表明|业内人士认为)", "evidence", "high", "moderate", "needs_source", "The statement invokes data or authority without identifying it.", "Add a verifiable source, date, and scope, or qualify the claim.", "native"),
    ("STRUCTURE-MECHANICAL-SECTIONS", r"(?:首先|其次|最后)[，,]", "structure", "low", "moderate", "style_choice", "Repeated ordinal transitions can make sections feel mechanically generated.", "Keep them only when they reflect a real sequence.", "native"),
]

ARMOR_FACT_RULES = {
    "esl-is-not-lcd": ("ARMOR-FACT-ESL-IS-NOT-LCD", r"\bESL\b[^.!?]{0,60}\b(?:is|are|means?|stands for|equals?)\b[^.!?]{0,30}\bLCD\b", "facts", "high", "moderate", "factual_conflict", "The copy equates ESL with LCD, which are distinct product categories.", "Verify the product category and do not equate ESL with LCD.", "armor-product-knowledge"),
    "esl-not-electrically-connected-to-power-track-without-evidence": ("ARMOR-FACT-ESL-POWER-TRACK-CONNECTION", r"\bESL\b[^.!?]{0,60}\b(?:electrically connected|wired|powered by|draws? power from)\b[^.!?]{0,30}\b(?:power track|track)\b", "facts", "high", "moderate", "needs_domain_review", "The copy asserts an electrical connection to the power track without confirmed evidence.", "Confirm the connection method or mark the claim for review.", "armor-product-knowledge"),
    "magnetic-light-needs-compatible-steel-surface": ("ARMOR-FACT-MAGNETIC-SURFACE-REQUIREMENT", r"\bmagnetic\b[^.!?]{0,70}\b(?:any surface|all surfaces|every surface|any shelf|all shelves|no surface preparation|no prep)\b", "facts", "high", "moderate", "needs_domain_review", "The copy implies magnetic lights work on any surface.", "State the ferromagnetic surface requirement or alternative mounting method.", "armor-product-knowledge"),
    "no-unsupported-zero-install-cost-or-roi": ("ARMOR-FACT-UNSUPPORTED-ZERO-INSTALL-ROI", r"\b(?:zero|no|free)\s+install(?:ation)?\s+cost\b|\bROI\b[^.!?]{0,40}\d+(?:\.\d+)?\s*%|\b\d+(?:\.\d+)?\s*%\s+ROI\b", "facts", "high", "moderate", "unsupported_claim", "The copy states zero install cost or a specific ROI figure without a supporting source.", "Add verified case data or qualify/remove the claim.", "armor-product-knowledge"),
    "verify-voltage-and-connection": ("ARMOR-FACT-VERIFY-VOLTAGE-CONNECTION", r"\b\d{2,4}\s*[Vv]\b", "facts", "medium", "low", "needs_domain_review", "The copy gives a specific voltage or connection value that requires product verification.", "Verify it against product documentation or mark it for review.", "armor-product-knowledge"),
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def parse_inline_list(text: str, key: str) -> list[str]:
    match = re.search(rf"^\s*{re.escape(key)}:\s*\[([^\]]*)\]", text, re.M)
    if not match:
        return []
    return [item.strip().strip("\"'") for item in match.group(1).split(",") if item.strip()]


def parse_inline_map(text: str, key: str) -> dict[str, float]:
    match = re.search(rf"^\s*{re.escape(key)}:\s*\{{([^}}]*)\}}", text, re.M)
    result: dict[str, float] = {}
    if not match:
        return result
    for item in match.group(1).split(","):
        if ":" not in item:
            continue
        name, value = item.split(":", 1)
        try:
            result[name.strip()] = float(value.strip())
        except ValueError:
            continue
    return result


def load_profiles(profile_ids: Iterable[str]) -> dict[str, Any]:
    merged: dict[str, Any] = {"focus": set(), "facts": set(), "exceptions": set(), "protect": set(), "weights": {}}
    loaded = []
    for profile_id in profile_ids:
        path = PROFILES_DIR / f"{profile_id}.yaml"
        if not path.is_file():
            raise ValueError(f"unknown profile: {profile_id}")
        text = path.read_text(encoding="utf-8")
        loaded.append(profile_id)
        for key in ("focus", "facts", "exceptions", "protect"):
            merged[key].update(parse_inline_list(text, key))
        merged["weights"].update(parse_inline_map(text, "weights"))
    merged["loaded"] = loaded
    return merged


def active_native_rule_ids() -> set[str]:
    if not NATIVE_RULES.is_file():
        return set()
    return set(re.findall(r"^\s*-\s+id:\s*([A-Z0-9-]+)\s*$", NATIVE_RULES.read_text(encoding="utf-8"), re.M))


def ruleset_fingerprint() -> str:
    paths = [Path(__file__).resolve(), ROOT / "upstream" / "upstream-lock.yaml", NATIVE_RULES]
    paths.extend(sorted(PROFILES_DIR.glob("*.yaml")))
    digest = hashlib.sha256()
    for path in sorted((p for p in paths if p.is_file()), key=lambda p: str(p.relative_to(ROOT))):
        digest.update(str(path.relative_to(ROOT)).encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def protected_spans(text: str) -> list[tuple[int, int]]:
    spans = []
    for pattern in (r"(?ms)^---\n.*?\n---\n", r"(?ms)```.*?```", r"(?m)^>.*$", r"(?ms)(?m)^\|.*(?:\n\|.*)+"):
        spans.extend((m.start(), m.end()) for m in re.finditer(pattern, text))
    return sorted(spans)


def is_protected(start: int, end: int, spans: Iterable[tuple[int, int]]) -> bool:
    return any(start < b and end > a for a, b in spans)


def detect_language(text: str) -> str:
    return "zh" if len(re.findall(r"[\u4e00-\u9fff]", text)) > len(re.findall(r"[A-Za-z]", text)) else "en"


def finding(rule_id: str, category: str, severity: str, confidence: str, evidence: str, start: int, end: int, diagnosis: str, action: str, repair_type: str, sources: tuple[str, ...], protected: bool = False) -> Finding:
    return Finding(rule_id, "local-static-scanner", category, severity, confidence, evidence, start, end, diagnosis, action, repair_type, sources, protected)


def paragraph_blocks(text: str, language: str, protected: list[tuple[int, int]]) -> list[tuple[int, int, int, str]]:
    blocks = []
    for match in re.finditer(r"(?ms)(?:^|\n\s*\n)([^\n].*?)(?=\n\s*\n|\Z)", text):
        raw = match.group(1).strip()
        if not raw or raw.startswith(("#", ">", "```", "|", "- ", "* ", "<!--")):
            continue
        start, end = match.start(1), match.end(1)
        if is_protected(start, end, protected):
            continue
        size = len(re.findall(r"[\u4e00-\u9fff]", raw)) if language == "zh" else len(re.findall(r"\b\w+\b", raw))
        if size >= (30 if language == "zh" else 20):
            blocks.append((start, end, size, raw))
    return blocks


def structural_findings(text: str, language: str, protected: list[tuple[int, int]], native_ids: set[str]) -> list[Finding]:
    results: list[Finding] = []
    body_match = re.match(r"(?s)^\s*---\s*\n.*?\n---\s*\n(.*)$", text)
    body_start = body_match.start(1) if body_match else 0
    body = body_match.group(1) if body_match else text
    opening = next((m for m in re.finditer(r"(?ms)^(?!#|\s*$)(.+?)(?=\n\s*\n|\Z)", body) if len(m.group(1).strip()) > 20), None)
    scene_re = re.compile(r"\b(?:walk into (?:a|any|the) (?:store|shop|supermarket)|picture yourself|imagine (?:walking|you are)|we (?:saw|noticed|found) (?:in|at) (?:a|the) store|customers? (?:tell|told) us)\b", re.I)
    if opening:
        scene = scene_re.search(opening.group(1))
        if scene:
            start = body_start + opening.start(1) + scene.start()
            results.append(finding("STRUCTURE-UNSUPPORTED-SCENE", "structure", "high", "high", scene.group(0), start, start + len(scene.group(0)), "The opening uses a generic field scene or attributed experience that cannot be verified from the article.", "Supply a traceable experience source or replace the scene with a direct, evidence-bounded problem or decision.", "needs_source", ("native",)))

    if "STRUCTURE-TEMPLATE-ENDCAP" in native_ids:
        endcap = re.compile(r"(?im)^#{1,6}\s*(?:总结|结论|常见问题(?:解答)?|FAQ|Summary|Conclusion|Frequently Asked Questions)\s*$")
        for match in endcap.finditer(text):
            results.append(finding("STRUCTURE-TEMPLATE-ENDCAP", "structure", "low", "high", match.group(0).strip(), match.start(), match.end(), "A labeled summary, conclusion, or FAQ is a predictable end-cap and may repeat the article.", "Keep it only for a distinct reader need; otherwise end with the decision, implication, limitation, or next action.", "style_choice", ("native",), is_protected(match.start(), match.end(), protected)))

    blocks = paragraph_blocks(text, language, protected)
    if "STRUCTURE-PARAGRAPH-UNIFORMITY" in native_ids and len(blocks) >= 4:
        sizes = [item[2] for item in blocks]
        mean = sum(sizes) / len(sizes)
        deviation = (sum((size - mean) ** 2 for size in sizes) / len(sizes)) ** 0.5
        if mean and deviation / mean <= 0.14:
            results.append(finding("STRUCTURE-PARAGRAPH-UNIFORMITY", "structure", "medium", "moderate", f"{len(blocks)} similarly sized paragraphs ({min(sizes)}–{max(sizes)} {'characters' if language == 'zh' else 'words'})", blocks[0][0], blocks[-1][1], "Paragraphs have unusually uniform length, which can reflect padded parallel generation.", "Allocate depth by information value; do not vary length mechanically.", "style_choice", ("native",)))

    density_terms = r"(?:提升|促进|推动|助力|赋能|优化|实现|打造|构建)" if language == "zh" else r"\b(?:improve|enhance|enable|empower|optimize|transform|streamline|drive)\w*\b"
    if "CONTENT-ABSTRACT-BENEFIT-DENSITY" in native_ids:
        for start, end, _, raw in blocks:
            if len(re.findall(density_terms, raw, re.I)) >= 3:
                results.append(finding("CONTENT-ABSTRACT-BENEFIT-DENSITY", "content_quality", "medium", "moderate", raw[:220], start, end, "The paragraph stacks benefit verbs without enough mechanism, condition, or trade-off.", "Keep the strongest supported benefit and connect it to a specific mechanism or source.", "needs_specificity", ("native",)))
    return results


def profile_findings(text: str, language: str, config: dict[str, Any], protected: list[tuple[int, int]]) -> list[Finding]:
    results: list[Finding] = []
    focus = config["focus"]
    if "faq-template" in focus or "answer-template" in focus:
        questions = list(re.finditer(r"(?im)^#{2,6}\s+[^\n?？]*[?？]\s*$", text))
        if len(questions) >= 3:
            first, last = questions[0], questions[-1]
            results.append(finding("SEO-ANSWER-TEMPLATE", "structure", "medium", "high", f"{len(questions)} heading-form questions in one article", first.start(), last.end(), "The article uses a repeated answer-template sequence that may duplicate the body.", "Retain only questions with a distinct reference need; integrate the rest into the argument.", "style_choice", ("profile:seo-geo",)))
    if "keyword-repetition" in focus:
        keyword_match = re.search(r"(?im)^seo_keywords:\s*[\"']?([^,\n\"']+)", text)
        if keyword_match:
            phrase = keyword_match.group(1).strip().lower()
            words = re.findall(r"\b[\w'-]+\b", text.lower())
            occurrences = len(re.findall(rf"\b{re.escape(phrase)}\b", text, re.I))
            density = occurrences * max(1, len(phrase.split())) / max(1, len(words)) * 100
            if occurrences >= 6 and density >= 1.5:
                results.append(finding("SEO-KEYWORD-REPETITION", "language", "medium", "high", f"'{phrase}' appears {occurrences} times; token density {density:.2f}%", keyword_match.start(1), keyword_match.end(1), "The primary keyword is repeated often enough to shape the prose mechanically.", "Use natural variants only where they preserve meaning; do not optimize toward a density target.", "style_choice", ("profile:seo-geo",)))
    if "pseudo-facts" in focus:
        pseudo = re.compile(r"\b(?:nobody|everyone|always|never)\b[^.!?]{0,90}(?:\.|!|\?)|\b(?:became|is now) the baseline\b", re.I)
        for match in pseudo.finditer(text):
            if not is_protected(match.start(), match.end(), protected):
                results.append(finding("CONTENT-CATEGORICAL-INDUSTRY-CLAIM", "evidence", "high", "moderate", match.group(0).strip(), match.start(), match.end(), "The sentence presents a categorical industry claim without establishing scope or evidence.", "Name the source and scope, qualify the claim, or remove it.", "needs_source", ("profile:seo-geo",)))
    if {"generic-benefits", "missing-mechanism", "exaggerated-claims"}.intersection(focus):
        generic = re.compile(r"\b(?:boosts? (?:sales|efficiency|engagement)|drives? (?:growth|conversion|results)|delivers? (?:better|exceptional|outstanding) (?:results|performance|experience)|earns? its keep)\b", re.I)
        for match in generic.finditer(text):
            results.append(finding("B2B-MISSING-MECHANISM", "content_quality", "medium", "moderate", match.group(0), match.start(), match.end(), "The B2B benefit claim lacks an explicit mechanism, condition, or evidence boundary.", "Name the changed step, mechanism, applicable condition, and remaining limitation.", "needs_specificity", ("profile:b2b-marketing",)))
    return results


def armor_fact_findings(text: str, fact_ids: Iterable[str], protected: list[tuple[int, int]]) -> list[Finding]:
    results = []
    for fact_id in fact_ids:
        rule = ARMOR_FACT_RULES.get(fact_id)
        if not rule:
            continue
        rule_id, pattern, category, severity, confidence, repair_type, diagnosis, action, source = rule
        for match in re.finditer(pattern, text, re.I):
            results.append(finding(rule_id, category, severity, confidence, match.group(0).strip(), match.start(), match.end(), diagnosis, action, repair_type, (source,), is_protected(match.start(), match.end(), protected)))
    return results


def scan_text(text: str, context: AuditContext, profile_config: dict[str, Any] | None = None) -> list[Finding]:
    language = detect_language(text) if context.language == "auto" else context.language
    config = profile_config or load_profiles(context.profile_ids)
    protected = protected_spans(text)
    patterns = (ZH_PATTERNS if language == "zh" else EN_PATTERNS) + (EN_PATTERNS if language == "zh" else [])
    results: list[Finding] = []
    for rule_id, pattern, category, severity, confidence, repair_type, diagnosis, action, sources in patterns:
        for match in re.finditer(pattern, text, re.I):
            if not match.group(0).strip() or is_protected(match.start(), match.end(), protected):
                continue
            results.append(finding(rule_id, category, severity, confidence, match.group(0).strip(), match.start(), match.end(), diagnosis, action, repair_type, tuple(sources.split(";"))))
    results.extend(armor_fact_findings(text, config["facts"], protected))
    results.extend(structural_findings(text, language, protected, active_native_rule_ids()))
    results.extend(profile_findings(text, language, config, protected))
    return results


def merge_findings(findings: list[Finding]) -> list[Finding]:
    merged: list[Finding] = []
    for item in sorted(findings, key=lambda value: (value.start_offset or 0, value.rule_id)):
        existing = next((value for value in merged if value.rule_id == item.rule_id and value.start_offset is not None and item.start_offset is not None and abs(value.start_offset - item.start_offset) <= max(len(value.evidence), len(item.evidence))), None)
        if not existing:
            merged.append(item)
            continue
        sources = tuple(dict.fromkeys(existing.upstream_sources + item.upstream_sources))
        confidence = "high" if len(sources) > 1 and existing.confidence != "low" else existing.confidence
        merged[merged.index(existing)] = replace(existing, confidence=confidence, upstream_sources=sources, protected=existing.protected or item.protected)
    return merged


def dimension_for(finding_item: Finding) -> str:
    if finding_item.category in {"evidence", "facts"}:
        return "evidence_deficiency"
    if finding_item.category == "content_quality":
        return "generic_claims"
    if finding_item.category in {"language", "chatbot_artifact", "sentence_structure"}:
        return "template_language"
    if finding_item.category == "structure":
        return "structural_uniformity"
    return "missing_constraints"


def risk(findings: list[Finding], weights: dict[str, float]) -> tuple[str, int, dict[str, int]]:
    dimensions = {key: 0 for key in DIMENSIONS}
    for item in findings:
        key = dimension_for(item)
        weighted = round(SEVERITY_VALUE[item.severity] * weights.get(key, 1.0))
        dimensions[key] = min(100, max(dimensions[key], weighted))
    score = max(dimensions.values(), default=0)
    level = "low" if score <= 20 else "moderate" if score <= 45 else "high" if score <= 70 else "critical"
    if any(item.severity == "high" and item.category in {"structure", "evidence", "facts", "chatbot_artifact"} for item in findings):
        level = "high" if level in {"low", "moderate"} else level
    if any(item.severity == "critical" for item in findings):
        level = "critical"
    return level, score, dimensions


def sentence_location(text: str, offset: int | None) -> dict[str, int]:
    if offset is None:
        return {}
    before = text[:offset]
    return {"paragraph": before.count("\n\n") + 1, "sentence": max(1, len(re.findall(r"[.!?。！？]", before)) + 1), "start_offset": offset}


def stable_finding_id(item: Finding) -> str:
    raw = f"{item.rule_id}\0{item.start_offset}\0{item.evidence}".encode("utf-8")
    return "F-" + sha256_bytes(raw)[:12].upper()


def adapter_status(disabled: list[str], local_enabled: bool) -> dict[str, dict[str, Any]]:
    statuses: dict[str, dict[str, Any]] = {
        "local-static-scanner": {"status": "success" if local_enabled else "disabled_by_user"},
        "conorbronsdon-avoid-ai-writing": {"status": "reference_only", "reason": "rules/provenance reference; no adapter code executed"},
        "blader-humanizer": {"status": "reference_only", "reason": "rules/provenance reference; no adapter code executed"},
        "harshaneel-humanize": {"status": "unavailable", "reason": "deferred adapter not enabled"},
        "aboudjem-humanizer-skill": {"status": "unavailable", "reason": "deferred adapter not enabled"},
        "gabelul-slopbuster": {"status": "unavailable", "reason": "optional CLI not installed"},
    }
    for name in disabled:
        if name in statuses:
            statuses[name] = {"status": "disabled_by_user"}
    return statuses


def build_report(text: str, language: str, profiles: list[str], config: dict[str, Any], findings: list[Finding], disabled: list[str], local_enabled: bool) -> dict[str, Any]:
    level, score, dimensions = risk(findings, config["weights"])
    output = []
    for item in findings:
        data = item.to_dict()
        data["id"] = stable_finding_id(item)
        data["location"] = sentence_location(text, item.start_offset)
        data.pop("start_offset", None)
        data.pop("end_offset", None)
        data.pop("protected", None)
        data["supported_by"] = [{"source": source} for source in item.upstream_sources]
        output.append(data)
    return {
        "schema_version": 2,
        "tool_version": TOOL_VERSION,
        "mode": "detect",
        "language": detect_language(text) if language == "auto" else language,
        "profiles": profiles,
        "profile_configuration": {
            "focus": sorted(config["focus"]),
            "exceptions": sorted(config["exceptions"]),
            "protect": sorted(config["protect"]),
            "weights": config["weights"],
        },
        "risk": {"level": level, "score": score, "dimensions": dimensions, "interpretation": "Editorial AI-style risk, not authorship probability."},
        "adapter_status": adapter_status(disabled, local_enabled),
        "findings": output,
        "limitations": [
            "Deterministic scan only; semantic judgment, voice reconstruction, and full repair require the Agent workflow in SKILL.md.",
            "A low result means no configured high-impact deterministic signal was found; it does not establish human authorship or editorial quality.",
        ],
        "reproducibility": {
            "input_sha256": sha256_bytes(text.encode("utf-8")),
            "ruleset_sha256": ruleset_fingerprint(),
            "stable_finding_ids": True,
        },
        "provenance": {
            "lock_file": "upstream/upstream-lock.yaml",
            "native_rule_file": "rules/native/voice-optimization.yaml",
            "active_native_rules": sorted(active_native_rule_ids()),
        },
    }


def markdown(report: dict[str, Any]) -> str:
    lines = ["# AI writing audit", "", "## Overall assessment", "", f"AI-style editorial risk: {report['risk']['level'].title()} ({report['risk']['score']})", "", report["risk"]["interpretation"], "", "## Reproducibility", "", f"- Tool: {report['tool_version']}", f"- Input SHA-256: `{report['reproducibility']['input_sha256']}`", f"- Ruleset SHA-256: `{report['reproducibility']['ruleset_sha256']}`", "", "## Adapter status", ""]
    lines.extend(f"- {name}: {value['status']}" + (f" ({value.get('reason')})" if value.get("reason") else "") for name, value in report["adapter_status"].items())
    lines.extend(["", "## Priority findings", ""])
    if not report["findings"]:
        lines.append("No deterministic findings. This does not establish human authorship or editorial quality.")
    for item in report["findings"]:
        lines.extend([f"### {item['id']} — {item['rule_id']}", "", f"Evidence: `{item['evidence']}`", f"Diagnosis: {item['diagnosis']}", f"Action: {item['action']}", f"Repair type: `{item['repair_type']}`", f"Supported by: {', '.join(source['source'] for source in item['supported_by'])}", ""])
    return "\n".join(lines)


def unsupported_mode(mode: str, output_format: str) -> int:
    message = f"Mode '{mode}' is agent-led and is not implemented by the deterministic CLI. Use --mode detect, then follow SKILL.md for full repair."
    if output_format == "json":
        print(json.dumps({"error": "unsupported_cli_mode", "mode": mode, "message": message}, ensure_ascii=False))
    else:
        print(message, file=sys.stderr)
    return 2


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Offline deterministic AI-style editorial-risk audit")
    parser.add_argument("article")
    parser.add_argument("--mode", choices=("detect", "repair", "edit", "compare"), default="detect")
    parser.add_argument("--language", choices=("auto", "en", "zh"), default="auto")
    parser.add_argument("--profile", default="general")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    parser.add_argument("--output")
    parser.add_argument("--adapter", action="append")
    parser.add_argument("--disable-adapter", action="append", default=[])
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--explain", action="store_true")
    args = parser.parse_args(argv)
    if args.mode != "detect":
        return unsupported_mode(args.mode, args.format)
    try:
        text = Path(args.article).read_text(encoding="utf-8")
        profile_ids = [item.strip() for item in args.profile.split(",") if item.strip()]
        config = load_profiles(profile_ids)
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"audit error: {exc}", file=sys.stderr)
        return 2
    local_enabled = not args.adapter or "local-static-scanner" in args.adapter
    context = AuditContext(args.language, args.mode, tuple(profile_ids))
    findings = merge_findings(scan_text(text, context, config)) if local_enabled else []
    report = build_report(text, args.language, profile_ids, config, findings, args.disable_adapter, local_enabled)
    rendered = json.dumps(report, ensure_ascii=False, indent=2) if args.format == "json" else markdown(report)
    if args.output:
        Path(args.output).write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)
    return 2 if args.strict and findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
