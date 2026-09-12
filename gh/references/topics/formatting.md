# Formatting

For commands supporting structured output:

- `--json field1,field2` selects fields; pass `--json` without fields to list valid names.
- `--jq '<expr>'` filters JSON with embedded jq; external jq is unnecessary.
- `--template '<template>'` formats JSON with Go templates and the helpers below.

## Template helpers
- `autocolor`: like `color`, but only emits color to terminals
- `color <style> <input>`: colorize input
- `join <sep> <list>`: joins values in the list using a separator
- `pluck <field> <list>`: collects values of a field from all items in the input
- `tablerow <fields>...`: aligns fields in output vertically as a table
- `tablerender`: renders fields added by tablerow in place
- `timeago <time>`: renders a timestamp as relative to now
- `timefmt <format> <time>`: formats a timestamp using Go's `Time.Format` function
- `truncate <length> <input>`: ensures input fits within length
- `hyperlink <url> <text>`: renders a terminal hyperlink
- `contains <arg> <string>`: checks if `string` contains `arg`
- `hasPrefix <prefix> <string>`: checks if `string` starts with `prefix`
- `hasSuffix <suffix> <string>`: checks if `string` ends with `suffix`
- `regexMatch <regex> <string>`: checks if `string` has any matches for `regex`

## Minimal patterns

```bash
gh pr list --json number,title,author
gh pr list --json author --jq '.[].author.login'
gh issue list --json title,url --template '{{range .}}{{hyperlink .url .title}}{{"\n"}}{{end}}'
```
