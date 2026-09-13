# Details

## Description

List gists from your user account.

You can use a regular expression to filter the description, file names,
or even the content of files in the gist using `--filter`.

For supported regular expression syntax, see <https://pkg.go.dev/regexp/syntax>.

Use `--include-content` to include content of files, noting that
this will be slower and increase the rate limit used. Instead of printing a table,
code will be printed with highlights similar to `gh search code`:

	{{gist ID}} {{file name}}
	    {{description}}
	        {{matching lines from content}}

No highlights or other color is printed when output is redirected.
