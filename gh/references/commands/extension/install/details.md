# Details

## Description

Install a GitHub CLI extension from a GitHub or local repository.

For GitHub repositories, the repository argument can be specified in
`OWNER/REPO` format or as a full repository URL.
The URL format is useful when the repository is not hosted on `github.com`.

For remote repositories, the GitHub CLI first looks for the release artifacts assuming
that it's a binary extension i.e. prebuilt binaries provided as part of the release.
In the absence of a release, the repository itself is cloned assuming that it's a
script extension i.e. prebuilt executable or script exists on its root.

The `--pin` flag may be used to specify a tag or commit for binary and script
extensions respectively, the latest version is used otherwise.

For local repositories, often used while developing extensions, use `.` as the
value of the repository argument. Note the following:

- After installing an extension from a locally cloned repository, the GitHub CLI will
manage this extension as a symbolic link (or equivalent mechanism on Windows) pointing
to an executable file with the same name as the repository in the repository's root.
For example, if the repository is named `gh-foobar`, the symbolic link will point
to `gh-foobar` in the extension repository's root.
- When executing the extension, the GitHub CLI will run the executable file found
by following the symbolic link. If no executable file is found, the extension
will fail to execute.
- If the extension is precompiled, the executable file must be built manually and placed
in the repository's root.

For the list of available extensions, see <https://github.com/topics/gh-extension>.
