# Options

## Flags

  -a, --assignee login       Assign people by their login. Use "@me" to self-assign.
      --attach file          Attach an image or video file, in '<file>#<image alt text>' format
      --blocked-by numbers   Mark the new issue as blocked by these issue numbers or URLs
      --blocking numbers     Mark the new issue as blocking these issue numbers or URLs
  -b, --body string          Supply a body. Will prompt for one otherwise.
  -F, --body-file file       Read body text from file (use "-" to read from standard input)
  -e, --editor               Skip prompts and open the text editor to write the title and body in. The first line is the title and the remaining text is the body.
  -l, --label name           Add labels by name
  -m, --milestone name       Add the issue to a milestone by name
      --parent number        Add the new issue as a sub-issue of the specified parent number or URL
  -p, --project title        Add the issue to projects by title
      --recover string       Recover input from a failed run of create
  -T, --template name        Template name to use as starting body text
  -t, --title string         Supply a title. Will prompt for one otherwise.
      --type name            Set the issue type by name
  -w, --web                  Open the browser to create an issue

## Inherited Flags

      --help                     Show help for command
  -R, --repo [HOST/]OWNER/REPO   Select another repository using the [HOST/]OWNER/REPO format
