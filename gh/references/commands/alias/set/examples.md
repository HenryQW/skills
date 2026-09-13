# Examples

  # Note: Command Prompt on Windows requires using double quotes for arguments
  $ gh alias set pv 'pr view'
  $ gh pv -w 123  #=> gh pr view -w 123

  $ gh alias set bugs 'issue list --label=bugs'
  $ gh bugs

  $ gh alias set homework 'issue list --assignee @me'
  $ gh homework

  $ gh alias set 'issue mine' 'issue list --mention @me'
  $ gh issue mine

  $ gh alias set epicsBy 'issue list --author="$1" --label="epic"'
  $ gh epicsBy vilmibm  #=> gh issue list --author="vilmibm" --label="epic"

  $ gh alias set --shell igrep 'gh issue list --label="$1" | grep "$2"'
  $ gh igrep epic foo  #=> gh issue list --label="epic" | grep "foo"
