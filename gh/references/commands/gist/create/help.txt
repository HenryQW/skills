Create a new GitHub gist with given contents.

Gists can be created from one or multiple files. Alternatively, pass `-` as
filename to read from standard input.

By default, gists are secret; use `--public` to make publicly listed ones.


USAGE
  gh gist create [<filename>... | <pattern>... | -] [flags]

ALIASES
  gh gist new

FLAGS
  -d, --desc string       A description for this gist
  -f, --filename string   Provide a filename to be used when reading from standard input
  -p, --public            List the gist publicly (default "secret")
  -w, --web               Open the web browser with created gist

INHERITED FLAGS
  --help   Show help for command

EXAMPLES
  # Publish file 'hello.py' as a public gist
  $ gh gist create --public hello.py

  # Create a gist with a description
  $ gh gist create hello.py -d "my Hello-World program in Python"

  # Create a gist containing several files
  $ gh gist create hello.py world.py cool.txt

  # Create a gist containing several files using patterns
  $ gh gist create *.md *.txt artifact.*

  # Read from standard input to create a gist
  $ gh gist create -

  # Create a gist from output piped from another command
  $ cat cool.txt | gh gist create

LEARN MORE
  Use `gh <command> <subcommand> --help` for more information about a command.
  Read the manual at https://cli.github.com/manual
  Learn about exit codes using `gh help exit-codes`
  Learn about accessibility experiences using `gh help accessibility`
