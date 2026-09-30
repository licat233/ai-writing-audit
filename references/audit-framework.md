# Audit framework

The local scanner combines deterministic pattern findings with conservative scoring. A match is evidence for editorial review, never an authorship conclusion. v0.3 reports the maximum weighted risk dimension rather than averaging empty dimensions, so a high-impact structural, evidence, or fact finding cannot be diluted to LOW.

Normalized rule families include `LANGUAGE-AI-VOCABULARY-CLUSTER`, `SENTENCE-NEGATIVE-PARALLELISM`, `SENTENCE-RULE-OF-THREE`, `FORMAT-DASH-DENSITY`, `CONTENT-GENERIC-CLAIM`, `CONTENT-EVIDENCE-GAP`, `STRUCTURE-MECHANICAL-SECTIONS`, and `CHATBOT-ARTIFACT`.

v0.3.1 adds conservative editorial-structure families: `STRUCTURE-INTRO-SECTION-OVERLAP`, `EVIDENCE-UNSUPPORTED-AUDIENCE-BEHAVIOR`, `STRUCTURE-ROADMAP-LIST-COUNT`, and the profile-gated `STRUCTURE-SPEC-TOUR-SEQUENCE`. Keyword-frequency/density metrics run on prose only: YAML front matter and JSON-LD/schema HTML comments are excluded so metadata cannot inflate repetition scores, while other findings keep their original offsets and locations.

When findings overlap, merge by rule, sentence/paragraph location, and similar evidence. Keep provenance from every supporting adapter. Multiple sources may increase confidence by one level, but weak signals cannot become critical merely by repetition.

Risk levels: 0–20 low, 21–45 moderate, 46–70 high, 71–100 critical. High-severity structure, evidence, fact, or chatbot findings impose a HIGH floor. These are editorial risk bands. Short documents and protected-heavy documents should carry a limitation.
