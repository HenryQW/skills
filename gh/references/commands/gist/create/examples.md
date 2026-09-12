# Examples

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
