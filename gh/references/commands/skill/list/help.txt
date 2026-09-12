List installed agent skills across known agent host directories.

By default, scans all supported agent hosts in both project and user scope.
Use `--agent` to scan one host, `--scope` to scan only project or user
scope, or `--dir` to scan a custom skills directory.

Project-scope skills are discovered relative to the current git repository
root. User-scope skills are discovered relative to your home directory.

For more information about output formatting flags, see `gh help formatting`.

USAGE
  gh skill list [flags]

ALIASES
  gh skill ls, gh skills ls

FLAGS
      --agent string      Filter by target agent: {github-copilot|claude-code|cursor|codex|gemini-cli|antigravity|antigravity-cli|antigravity2.0|adal|amp|augment|bob|cline|codebuddy|command-code|continue|cortex|crush|deepagents|devin|droid|firebender|goose|grok|iflow-cli|junie|kilo|kimi-cli|kiro-cli|kode|mcpjam|mistral-vibe|mux|neovate|openclaw|opencode|openhands|pi|pochi|qoder|qwen-code|replit|roo|trae|trae-cn|universal|warp|zencoder}
      --dir string        Scan a custom directory for installed skills
  -q, --jq expression     Filter JSON output using a jq expression
      --json fields       Output JSON with the specified fields
      --scope string      Filter by installation scope: {project|user}
  -t, --template string   Format JSON output using a Go template; see "gh help formatting"

INHERITED FLAGS
  --help   Show help for command

JSON FIELDS
  agentHosts, path, pinned, scope, skillName, sourceURL, version

EXAMPLES
  # List all installed skills
  $ gh skill list

  # List skills installed for GitHub Copilot
  $ gh skill list --agent github-copilot

  # List user-scope skills
  $ gh skill list --scope user

  # List skills as JSON
  $ gh skill list --json skillName,sourceURL,scope,version,pinned,path

LEARN MORE
  Use `gh <command> <subcommand> --help` for more information about a command.
  Read the manual at https://cli.github.com/manual
  Learn about exit codes using `gh help exit-codes`
  Learn about accessibility experiences using `gh help accessibility`
