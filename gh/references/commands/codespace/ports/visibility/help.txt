Change the visibility of the forwarded port

USAGE
  gh codespace ports visibility <port>:{public|private|org}... [flags]

INHERITED FLAGS
  -c, --codespace string    Name of the codespace
      --help                Show help for command
  -R, --repo string         Filter codespace selection by repository name (user/repo)
      --repo-owner string   Filter codespace selection by repository owner (username or org)

EXAMPLES
  $ gh codespace ports visibility 80:org 3000:private 8000:public

LEARN MORE
  Use `gh <command> <subcommand> --help` for more information about a command.
  Read the manual at https://cli.github.com/manual
  Learn about exit codes using `gh help exit-codes`
  Learn about accessibility experiences using `gh help accessibility`
