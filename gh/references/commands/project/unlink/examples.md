# Examples

  # Unlink monalisa's project 1 from her repository "my_repo"
  $ gh project unlink 1 --owner monalisa --repo my_repo

  # Unlink monalisa's organization's project 1 from her team "my_team"
  $ gh project unlink 1 --owner my_organization --team my_team

  # Unlink monalisa's project 1 from the repository of current directory if neither --repo nor --team is specified
  $ gh project unlink 1
