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
