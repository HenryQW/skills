# Examples

  # Create a stack with a new branch
  $ gh stack init my-feature

  # Create a multi-layer stack at once
  $ gh stack init auth-layer api-routes ui-components

  # Adopt existing branches into a stack (bottom to top)
  $ gh stack init feat/auth feat/api feat/ui

  # Specify a different trunk branch
  $ gh stack init --base develop my-feature
