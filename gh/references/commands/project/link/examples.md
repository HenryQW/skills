# Examples

  # Link monalisa's project 1 to her repository "my_repo"
  $ gh project link 1 --owner monalisa --repo my_repo

  # Link monalisa's organization's project 1 to her team "my_team"
  $ gh project link 1 --owner my_organization --team my_team

  # Link monalisa's project 1 to the repository of current directory if neither --repo nor --team is specified
  $ gh project link 1
