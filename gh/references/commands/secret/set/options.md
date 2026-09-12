# Options

## Flags

  -a, --app string           Set the application for a secret: {actions|agents|codespaces|dependabot}
  -b, --body string          The value for the secret (reads from standard input if not specified)
  -e, --env environment      Set deployment environment secret
  -f, --env-file file        Load secret names and values from a dotenv-formatted file
      --no-repos-selected    No repositories can access the organization secret
      --no-store             Print the encrypted, base64-encoded value instead of storing it on GitHub
  -o, --org organization     Set organization secret
  -r, --repos repositories   List of repositories that can access an organization or user secret
  -u, --user                 Set a secret for your user
  -v, --visibility string    Set visibility for an organization secret: {all|private|selected} (default "private")

## Inherited Flags

      --help                     Show help for command
  -R, --repo [HOST/]OWNER/REPO   Select another repository using the [HOST/]OWNER/REPO format
