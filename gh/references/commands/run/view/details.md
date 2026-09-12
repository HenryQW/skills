# Details

## Description

View a summary of a workflow run.

Due to platform limitations, `gh` may not always be able to associate jobs with their
corresponding logs when using the primary method of fetching logs in zip format.

In such cases, `gh` will attempt to fetch logs for each job individually via the API.
This fallback is slower and more resource-intensive. If more than 25 job logs are missing,
the operation will fail with an error.

Additionally, due to similar platform constraints, some log lines may not be
associated with a specific step within a job. In these cases, the step name will
appear as `UNKNOWN STEP` in the log output.

For more information about output formatting flags, see `gh help formatting`.

## Json Fields

  attempt, conclusion, createdAt, databaseId, displayTitle, event, headBranch,
  headSha, jobs, name, number, startedAt, status, updatedAt, url,
  workflowDatabaseId, workflowName
