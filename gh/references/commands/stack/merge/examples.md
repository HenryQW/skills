# Examples

  # Merge the current stack (interactive picker)
  $ gh stack merge

  # Merge a stack you don't have checked out, by stack number
  $ gh stack merge 7

  # Merge everything up to and including PR #42
  $ gh stack merge 42

  # Merge the whole current stack without prompting, squashing
  $ gh stack merge --yes --squash
