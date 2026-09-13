# Details

## Description

Install agent skills from a GitHub repository or local directory into
your local environment. Skills are placed in a host-specific directory
at either project scope (inside the current git repository) or user
scope (in your home directory, available everywhere).

A wide range of AI coding agents are supported, including GitHub
Copilot, Claude Code, Cursor, Codex, Gemini CLI, Antigravity, Amp,
Devin, Goose, Grok, Junie, OpenCode, and many more.

Supported `--agent` values:

  - GitHub Copilot (github-copilot)
  - Claude Code (claude-code)
  - Cursor (cursor)
  - Codex (codex)
  - Gemini CLI (gemini-cli)
  - Antigravity (antigravity)
  - Antigravity CLI (antigravity-cli)
  - Antigravity 2.0 (antigravity2.0)
  - AdaL (adal)
  - Amp (amp)
  - Augment (augment)
  - IBM Bob (bob)
  - Cline (cline)
  - CodeBuddy (codebuddy)
  - Command Code (command-code)
  - Continue (continue)
  - Cortex Code (cortex)
  - Crush (crush)
  - Deep Agents (deepagents)
  - Devin (devin)
  - Droid (droid)
  - Firebender (firebender)
  - Goose (goose)
  - Grok (grok)
  - iFlow CLI (iflow-cli)
  - Junie (junie)
  - Kilo Code (kilo)
  - Kimi Code CLI (kimi-cli)
  - Kiro CLI (kiro-cli)
  - Kode (kode)
  - MCPJam (mcpjam)
  - Mistral Vibe (mistral-vibe)
  - Mux (mux)
  - Neovate (neovate)
  - OpenClaw (openclaw)
  - OpenCode (opencode)
  - OpenHands (openhands)
  - Pi (pi)
  - Pochi (pochi)
  - Qoder (qoder)
  - Qwen Code (qwen-code)
  - Replit (replit)
  - Roo Code (roo)
  - Trae (trae)
  - Trae CN (trae-cn)
  - Universal (universal)
  - Warp (warp)
  - Zencoder (zencoder)

Use `--agent` and `--scope` to control placement, or `--dir` for a
custom directory. The default scope is `project`, and the default
agent is `github-copilot` (when running non-interactively).

At project scope, several agents (including GitHub Copilot, Cursor,
Codex, Gemini CLI, Antigravity, Amp, Cline, OpenCode, and Warp) share
the `.agents/skills` directory. If you select multiple hosts that
resolve to the same destination, each skill is installed there only once.

The first argument is a GitHub repository in `OWNER/REPO` format.
Use `--from-local` to install from a local directory instead.
Local skills are auto-discovered using the same conventions as remote
repositories, and files are copied (not symlinked) with local-path
tracking metadata injected into frontmatter.

Skills are discovered automatically using the `skills/*/SKILL.md` convention
defined by the Agent Skills specification, including when the `skills/`
directory is nested under a prefix (e.g. `terraform/code-generation/skills/...`).
For more information on the specification,
see: https://agentskills.io/specification

The skill argument can be a name, a namespaced name (`author/skill`),
or an exact path within the repository (`skills/author/skill`,
`packages/agent-skills/code-review`, or any `.../SKILL.md` path).
Namespaced names with one slash are matched by name. Use a `SKILL.md`
suffix to force a one-directory path outside the standard conventions.

Performance tip: when installing from a large repository with many
skills, providing an exact path instead of a skill name avoids a
full tree traversal of the repository, making the install significantly faster.

When a skill name is provided without a version, the CLI resolves the
version in this order:

  1. Latest tagged release in the repository
  2. Default branch HEAD

To pin to a specific version, either append `@VERSION` to the skill
name or use the `--pin` flag. The version is resolved as a git tag or commit SHA.

Installed skills have source tracking metadata injected into their
frontmatter. This metadata identifies the source repository and
enables `gh skill update` to detect changes.

When run interactively, the command prompts for any missing arguments.

Use `--all` to install every discovered skill from the repository
without prompting for skill selection. When run non-interactively,
`repository` is required; without a skill name or `--all` the
matching skills are listed (as tab-separated values when piped) so you can
browse or filter them with tools like `grep` before re-running with
a specific skill.
