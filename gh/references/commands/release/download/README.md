# gh release download

Download assets from a GitHub release.

**Usage:** `gh release download [<tag>] [flags]`

## Options
      --allow-escape-sequences   Allow printing terminal escape sequences when writing an asset to standard output
  -A, --archive format           Download the source code archive in the specified format (zip or tar.gz)
      --clobber                  Overwrite existing files of the same name
  -D, --dir directory            The directory to download files into (default ".")
  -O, --output file              The file to write a single asset to (use "-" to write to standard output)
  -p, --pattern stringArray      Download only assets that match a glob pattern
      --skip-existing            Skip downloading when files of the same name exist
  -R, --repo [HOST/]OWNER/REPO   Select another repository using the [HOST/]OWNER/REPO format

## More
- [Examples](examples.md)
- [Details](details.md)
