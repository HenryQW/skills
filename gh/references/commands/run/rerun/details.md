# Details

## Description

Rerun an entire run, only failed jobs, or a specific job from a run.

Note that due to historical reasons, the `--job` flag may not take what you expect.
Specifically, when navigating to a job in the browser, the URL looks like this:
`https://github.com/<owner>/<repo>/actions/runs/<run-id>/jobs/<number>`.

However, this `<number>` should not be used with the `--job` flag and will result in the
API returning `404 NOT FOUND`. Instead, you can get the correct job IDs using the following command:

	gh run view <run-id> --json jobs --jq '.jobs[] | {name, databaseId}'

You will need to use databaseId field for triggering job re-runs.
