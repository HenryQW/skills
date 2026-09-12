# Examples

  # Search code matching "react" and "lifecycle"
  $ gh search code react lifecycle

  # Search code matching "error handling"
  $ gh search code "error handling"

  # Search code using raw search qualifiers as separate arguments
  $ gh search code panic path:pkg language:go

  # Search code matching "deque" in Python files
  $ gh search code deque --language=python

  # Search code matching "cli" in repositories owned by microsoft organization
  $ gh search code cli --owner=microsoft

  # Search code matching "panic" in the GitHub CLI repository
  $ gh search code panic --repo cli/cli

  # Search code matching keyword "lint" in package.json files
  $ gh search code lint --filename package.json
