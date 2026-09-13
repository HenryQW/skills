# Details

## Description

Create a new autolink reference for a repository.

The `keyPrefix` argument specifies the prefix that will generate a link when it is appended by certain characters.

The `urlTemplate` argument specifies the target URL that will be generated when the keyPrefix is found, which
must contain `<num>` variable for the reference number.

By default, autolinks are alphanumeric with `--numeric` flag used to create a numeric autolink.

The `<num>` variable behavior differs depending on whether the autolink is alphanumeric or numeric:

- alphanumeric: matches `A-Z` (case insensitive), `0-9`, and `-`
- numeric: matches `0-9`

If the template contains multiple instances of `<num>`, only the first will be replaced.
