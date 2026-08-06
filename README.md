# ai-writing-audit

`ai-writing-audit` is a source-traceable local orchestration skill for detecting writing patterns that may create an AI-generated impression. It combines normalized local rules with provenance from established open-source projects and produces Markdown or JSON reports.

It measures AI-style writing risk. It does not determine who or what authored a text, and it does not output an AI-generation probability.

Phase 1 is offline and detect-first:

```bash
python3 /path/to/ai-writing-audit/scripts/audit.py article.md --mode detect --language auto --profile general --format markdown
python3 /path/to/ai-writing-audit/scripts/audit.py article.md --format json --output report.json
```

The scanner does not upload article content, does not modify the input by default, and treats quoted/code/table/front-matter text as protected.

The same folder can be installed as a Skill in Codex, Claude Code, or Hermes Agent. The runtime only needs Python 3.9+ and the standard library.
