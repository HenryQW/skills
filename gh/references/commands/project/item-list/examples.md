# Examples

  # List the items in the current users's project "1"
  $ gh project item-list 1 --owner "@me"

  # List items assigned to a specific user
  $ gh project item-list 1 --owner "@me" --query "assignee:monalisa"

  # List open issues assigned to yourself
  $ gh project item-list 1 --owner "@me" --query "assignee:@me is:issue is:open"

  # List items with the "bug" label that are not done
  $ gh project item-list 1 --owner "@me" --query "label:bug -status:Done"

  # Show the "Status" and "Priority" field values as extra columns
  $ gh project item-list 1 --owner "@me" --field "Status" --field "Priority"
