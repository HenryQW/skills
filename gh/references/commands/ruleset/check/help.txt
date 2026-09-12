View information about GitHub rules that apply to a given branch.

The provided branch name does not need to exist; rules will be displayed that would apply
to a branch with that name. All rules are returned regardless of where they are configured.

If no branch name is provided, then the current branch will be used.

The `--default` flag can be used to view rules that apply to the default branch of the
repository.


USAGE
  gh ruleset check [<branch>] [flags]

FLAGS
      --default   Check rules on default branch
  -w, --web       Open the branch rules page in a web browser

INHERITED FLAGS
      --help                     Show help for command
  -R, --repo [HOST/]OWNER/REPO   Select another repository using the [HOST/]OWNER/REPO format

EXAMPLES
  # View all rules that apply to the current branch
  $ gh ruleset check

  # View all rules that apply to a branch named "my-branch" in a different repository
  $ gh ruleset check my-branch --repo owner/repo

  # View all rules that apply to the default branch in a different repository
  $ gh ruleset check --default --repo owner/repo

  # View a ruleset configured in a different repository or any of its parents
  $ gh ruleset view 23 --repo owner/repo

  # View an organization-level ruleset
  $ gh ruleset view 23 --org my-org

LEARN MORE
  Use `gh <command> <subcommand> --help` for more information about a command.
  Read the manual at https://cli.github.com/manual
  Learn about exit codes using `gh help exit-codes`
  Learn about accessibility experiences using `gh help accessibility`
