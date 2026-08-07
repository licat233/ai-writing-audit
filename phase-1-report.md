# Phase 1 report

## Completed

- Created the installable `ai-writing-audit` skill with detect-first `SKILL.md`.
- Investigated and locked five upstream repositories with commit and license metadata.
- Added manifest, lock file, source registry, notices, profiles, finding/report schemas, and a standard-library-only offline CLI.
- Implemented English and Chinese static rules, protected-region recognition, basic finding deduplication, adapter status reporting, Markdown/JSON output, strict exit behavior, and tests.
- Enabled the `armor` profile: `audit.py` now reads `profiles/armor.yaml` and applies its `facts` list as `ARMOR-FACT-*` domain checks (ESL≠LCD, power-track connection needs evidence, magnetic lights need ferromagnetic surfaces, no unsupported zero-install-cost/ROI, verify voltage). A `facts`-category finding raises overall risk to at least `high`.
- Added provenance for the required `avoid-ai-writing` workflow and `blader/humanizer` pattern references without vendoring upstream code.

## Not completed

- Full executable adapters for `harshaneel/humanize`, `Aboudjem/humanizer-skill`, and `slopbuster`.
- Semantic repetition, mechanism, and paragraph-swapping analysis beyond deterministic rules.
- Repair, edit, compare, sync, license verification, and notice-generation scripts.
- Full 20-English/20-Chinese/non-native regression corpus.

## Known limitations

The Phase 1 scanner is conservative and deterministic. A finding is an editorial review signal, not evidence of authorship. Profile weighting beyond the `armor` facts list (per-profile weights and exceptions) is deferred.

## Test command

```bash
python3 -m unittest discover -s tests
```

## Next phase

Historical note: v0.3.0 completed the larger deterministic regression corpus, executable Profile focus/weights, reproducibility fingerprints, stable finding IDs, and truthful `reference_only` adapter status. Upstream reference adapters still do not execute third-party code, and deterministic file mutation remains intentionally disabled; full repair is agent-led through `SKILL.md` and `references/native-optimization.md`.
