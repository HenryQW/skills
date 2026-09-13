# Examples

  # Search repositories matching set of keywords "cli" and "shell"
  $ gh search repos cli shell

  # Search repositories matching phrase "vim plugin"
  $ gh search repos "vim plugin"

  # Search repositories using raw search qualifiers as separate arguments
  $ gh search repos topic:github 'stars:>5000'

  # Search repositories public repos in the microsoft organization
  $ gh search repos --owner=microsoft --visibility=public

  # Search repositories with a set of topics
  $ gh search repos --topic=unix,terminal

  # Search repositories by coding language and number of good first issues
  $ gh search repos --language=go --good-first-issues=">=10"

  # Search repositories without topic "linux"
  $ gh search repos -- -topic:linux

  # Search repositories excluding archived repositories
  $ gh search repos --archived=false
