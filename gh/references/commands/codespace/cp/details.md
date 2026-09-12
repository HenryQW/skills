# Details

## Description

The `cp` command copies files between the local and remote file systems.

As with the UNIX `cp` command, the first argument specifies the source and the last
specifies the destination; additional sources may be specified after the first,
if the destination is a directory.

The `--recursive` flag is required if any source is a directory.

A `remote:` prefix on any file name argument indicates that it refers to
the file system of the remote (Codespace) machine. It is resolved relative
to the home directory of the remote user.

By default, remote file names are interpreted literally. With the `--expand` flag,
each such argument is treated in the manner of `scp`, as a Bash expression to
be evaluated on the remote machine, subject to expansion of tildes, braces, globs,
environment variables, and backticks. For security, do not use this flag with arguments
provided by untrusted users; see <https://lwn.net/Articles/835962/> for discussion.

By default, the `cp` command will create a public/private ssh key pair to authenticate with
the codespace inside the `~/.ssh directory`.
