# Examples

  # List the first 30 extensions sorted by star count, descending
  $ gh ext search

  # List more extensions
  $ gh ext search --limit 300

  # List extensions matching the term "branch"
  $ gh ext search branch

  # List extensions owned by organization "github"
  $ gh ext search --owner github

  # List extensions, sorting by recently updated, ascending
  $ gh ext search --sort updated --order asc

  # List extensions, filtering by license
  $ gh ext search --license MIT

  # Open search results in the browser
  $ gh ext search -w
