This command will take over your terminal and run a fully interactive
interface for browsing, adding, and removing gh extensions. A terminal
width greater than 100 columns is recommended.

To learn how to control this interface, press `?` after running to see
the help text.

Press `q` to quit.

Running this command with `--single-column` should make this command
more intelligible for users who rely on assistive technology like screen
readers or high zoom.

For a more traditional way to discover extensions, see:

	gh ext search

along with `gh ext install`, `gh ext remove`, and `gh repo view`.


USAGE
  gh extension browse [flags]

FLAGS
      --debug           Log to /tmp/extBrowse-*
  -s, --single-column   Render TUI with only one column of text

INHERITED FLAGS
  --help   Show help for command

LEARN MORE
  Use `gh <command> <subcommand> --help` for more information about a command.
  Read the manual at https://cli.github.com/manual
  Learn about exit codes using `gh help exit-codes`
  Learn about accessibility experiences using `gh help accessibility`
