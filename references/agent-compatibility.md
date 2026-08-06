# Agent compatibility

## Shared contract

All supported agents use the same folder and the same `SKILL.md`. The only required runtime dependency is Python 3.9+; the audit CLI is offline and standard-library-only.

## Codex

Place or link the skill folder under the Codex skills directory, then invoke it by its name or by asking for an AI-writing audit. The bundled `agents/openai.yaml` supplies optional UI metadata. It is not required for execution.

## Claude Code

Copy or symlink this folder to the project's `.claude/skills/ai-writing-audit/` for project scope, or to the user's Claude skills directory for user scope. Claude Code should load `SKILL.md`, resolve the folder containing it, and run:

```bash
python3 /absolute/path/to/ai-writing-audit/scripts/audit.py article.md --mode detect --format markdown
```

Do not require Claude-specific hooks, MCP servers, or a network connection.

## Hermes Agent

Copy or symlink this folder to the Hermes skills directory. Hermes reads the standard frontmatter; `version`, `license`, `platforms`, and `metadata.hermes` provide discovery metadata. Hermes should invoke the same local CLI through its shell execution capability. The skill must not assume that the current directory is the skill directory.

## Portability rules

- Use `python3` where available; if a host exposes Python under another explicit executable, configure that host rather than changing the audit logic.
- Pass absolute paths when the agent's current directory is unknown.
- Keep article content local. Do not add network adapters or upload integrations without an explicit future feature and user consent.
- Treat missing optional adapters as a reported limitation, not a fatal error.
