# gh issue edit

Edit one or more issues within the same repository.

**Usage:** `gh issue edit {<numbers> | <urls>} [flags]`

## Options
      --add-assignee login         Add assigned users by their login. Use "@me" to assign yourself, or "@copilot" to assign Copilot.
      --add-blocked-by number      Add 'blocked by' relationships by issue number or URL
      --add-blocking number        Add 'blocking' relationships by issue number or URL
      --add-label name             Add labels by name
      --add-project title          Add the issue to projects by title
      --add-sub-issue number       Add sub-issues by number or URL
      --attach file                Attach an image or video file, in '<file>#<image alt text>' format
  -b, --body string                Set the new body.
  -F, --body-file file             Read body text from file (use "-" to read from standard input)
  -m, --milestone name             Edit the milestone the issue belongs to by name
      --parent number              Set the parent issue by number or URL
      --remove-assignee login      Remove assigned users by their login. Use "@me" to unassign yourself, or "@copilot" to unassign Copilot.
      --remove-blocked-by number   Remove 'blocked by' relationships by issue number or URL
      --remove-blocking number     Remove 'blocking' relationships by issue number or URL
      --remove-label name          Remove labels by name
      --remove-milestone           Remove the milestone association from the issue
      --remove-parent              Remove the parent issue
      --remove-project title       Remove the issue from projects by title
      --remove-sub-issue number    Remove sub-issues by number or URL
      --remove-type                Remove the issue type from the issue
  -t, --title string               Set the new title.
      --type name                  Set the issue type by name
  -R, --repo [HOST/]OWNER/REPO   Select another repository using the [HOST/]OWNER/REPO format

## More
- [Examples](examples.md)
- [Details](details.md)
