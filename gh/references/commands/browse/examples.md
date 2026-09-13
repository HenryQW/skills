# Examples

  # Open the home page of the current repository
  $ gh browse

  # Open the script directory of the current repository
  $ gh browse script/

  # Open issue or pull request 217
  $ gh browse 217

  # Open commit page
  $ gh browse 77507cd94ccafcf568f8560cfecde965fcfa63

  # Open repository settings
  $ gh browse --settings

  # Open main.go at line 312
  $ gh browse main.go:312

  # Open blame view for main.go at line 312
  $ gh browse main.go:312 --blame

  # Open main.go with the repository at head of bug-fix branch
  $ gh browse main.go --branch bug-fix

  # Open main.go with the repository at commit 775007cd
  $ gh browse main.go --commit=77507cd94ccafcf568f8560cfecde965fcfa63
