# ai-writing-audit

`ai-writing-audit` is a source-traceable local orchestration skill for detecting and repairing writing patterns that may create an AI-generated impression. It combines deterministic structural scanning with an agent-led, fact-preserving full-article rewrite workflow.

It measures AI-style writing risk. It does not determine who or what authored a text, and it does not output an AI-generation probability.

The v0.3 CLI performs an offline deterministic audit. Full repair is performed by the Agent using `SKILL.md` and `references/native-optimization.md`:

```bash
python3 /path/to/ai-writing-audit/scripts/audit.py article.md --mode detect --language auto --profile general --format markdown
python3 /path/to/ai-writing-audit/scripts/audit.py article.md --format json --output report.json
```

The scanner detects unsupported generic scene openings, template endings, answer-template repetition, abstract benefit density, uniform paragraph structure, formulaic language, evidence gaps, and selected domain risks. v0.3.1 adds conservative editorial-structure signals: lexical overlap between the introduction and the first headed section, unsupported generalized buyer/shopper behavior, article roadmap/list-count phrasing, and 4+ parallel H3 spec-tour sequences (profile-gated). Keyword density excludes YAML front matter and JSON-LD/schema comments so metadata cannot inflate repetition scores. It does not upload or modify article content and treats quoted/code/table/front-matter text as protected. `repair`, `edit`, and `compare` return `unsupported_cli_mode`; they can never be mistaken for a completed repair.

Each JSON report includes the input SHA-256, deterministic ruleset/config fingerprint, tool version, selected profile configuration, and stable finding IDs. Provenance-only upstream references are labeled `reference_only`, never `success`.

The same folder can be installed as a Skill in Codex, Claude Code, or Hermes Agent. The runtime only needs Python 3.9+ and the standard library.

## Full article polish

The Skill now supports an agent-led full repair workflow. Ask the agent explicitly:

```text
Use $ai-writing-audit to fully polish this article.
First audit it, then rewrite the complete article so it is more specific, coherent, natural, and consistent with the supplied facts and intended audience. Preserve quotes, code, tables, terminology, and factual limits. Do not invent data or personal experience. Return the diagnosis, the complete revised article, a change log, unresolved fact gaps, and a post-repair audit.
```

The repair workflow is not a synonym for “make it undetectable.” It improves editorial quality and reduces formulaic patterns while preserving truth, constraints, and the author's intended register. First-person experience, field details, dialogue, humor, and data are used only when supplied or attributable; the Agent must not invent them. See [`references/native-optimization.md`](references/native-optimization.md) for the full method.

## Installation

The repository is private. Make sure the agent or terminal is authenticated to GitHub as an account that can read `licat233/ai-writing-audit`.

### Install with an Agent

You can ask the agent directly:

```text
Install the private GitHub skill licat233/ai-writing-audit for this agent.
Clone it into the agent's user-level skills directory, verify SKILL.md, and run the bundled tests. Do not modify the source repository.
```

For a project-local installation:

```text
Install licat233/ai-writing-audit into this project's local skill directory and verify that the audit CLI can run on a Markdown file.
```

The agent should use a normal authenticated Git operation, preserve the repository contents, and report the final installation path and test result.

### Codex

```bash
git clone https://github.com/licat233/ai-writing-audit.git ~/.codex/skills/ai-writing-audit
python3 ~/.codex/skills/ai-writing-audit/scripts/audit.py ~/.codex/skills/ai-writing-audit/tests/fixtures/english.md --format markdown
```

Then ask: `Use $ai-writing-audit to audit this article for AI-style writing risk.`

### Claude Code

```bash
mkdir -p .claude/skills
git clone https://github.com/licat233/ai-writing-audit.git .claude/skills/ai-writing-audit
python3 .claude/skills/ai-writing-audit/scripts/audit.py article.md --mode detect
```

Then ask Claude Code to use the skill and specify whether the article may be modified.

### Hermes Agent

```bash
git clone https://github.com/licat233/ai-writing-audit.git ~/.hermes/skills/ai-writing-audit
python3 ~/.hermes/skills/ai-writing-audit/scripts/audit.py article.md --mode detect
```

Restart or reload Hermes skills if your installation caches the skill list. Hermes reads the same `SKILL.md`; no Hermes-specific plugin or MCP server is required.

### Private repository authentication

If HTTPS cloning asks for credentials, authenticate with GitHub CLI first:

```bash
gh auth login
gh auth status
git clone https://github.com/licat233/ai-writing-audit.git ~/.codex/skills/ai-writing-audit
```

Do not put a personal access token directly into a clone URL or commit it to a repository.

### Verify an installation

Run these commands from the installed skill directory:

```bash
python3 -m unittest discover -s tests -v
python3 /Users/licat/.codex/skills/.system/skill-creator/scripts/quick_validate.py .
```

If the second command is unavailable outside Codex, the CLI test and the first command are sufficient for Claude Code and Hermes Agent. Use the installed directory in place of the example path.

## Local regression

The `tests/test_audit.py::LocalRegressionTests` class audits two local rewrite fixtures when they are present and skips otherwise. Run the same check manually with:

```bash
python3 scripts/audit.py /private/tmp/armor-retail-rewrite.Bgsvyu/rewritten-index.md --profile b2b-marketing,seo-geo,armor --format json   # must NOT be low/clean
python3 scripts/audit.py /private/tmp/armor-retail-rewrite.Bgsvyu/rewritten-index-v3.md --profile b2b-marketing,seo-geo,armor --format json  # must stay low
```

A deterministic `low`/`PASS` result is a scan outcome, not an approval to publish: the human editorial gates in `references/native-optimization.md` still apply.
