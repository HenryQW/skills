# Details

## Description

List repositories owned by a user or organization.

Note that the list will only include repositories owned by the provided argument,
and the `--fork` or `--source` flags will not traverse ownership boundaries. For example,
when listing the forks in an organization, the output would not include those owned by individual users.

For more information about output formatting flags, see `gh help formatting`.

## Json Fields

  archivedAt, assignableUsers, codeOfConduct, contactLinks, createdAt,
  defaultBranchRef, deleteBranchOnMerge, description, diskUsage, forkCount,
  fundingLinks, hasDiscussionsEnabled, hasIssuesEnabled, hasProjectsEnabled,
  hasWikiEnabled, homepageUrl, id, isArchived, isBlankIssuesEnabled, isEmpty,
  isFork, isInOrganization, isMirror, isPrivate, isSecurityPolicyEnabled,
  isTemplate, isUserConfigurationRepository, issueTemplates, issues, labels,
  languages, latestRelease, licenseInfo, mentionableUsers, mergeCommitAllowed,
  milestones, mirrorUrl, name, nameWithOwner, openGraphImageUrl, owner, parent,
  primaryLanguage, projects, projectsV2, pullRequestTemplates, pullRequests,
  pushedAt, rebaseMergeAllowed, repositoryTopics, securityPolicyUrl,
  squashMergeAllowed, sshUrl, stargazerCount, templateRepository, updatedAt, url,
  usesCustomOpenGraphImage, viewerCanAdminister, viewerDefaultCommitEmail,
  viewerDefaultMergeMethod, viewerHasStarred, viewerPermission,
  viewerPossibleCommitEmails, viewerSubscription, visibility, watchers
