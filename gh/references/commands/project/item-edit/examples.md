# Examples

  # Set the "Status" field to "In Progress" for an issue on monalisa's project 1
  $ gh project item-edit 1 --owner monalisa --url https://github.com/monalisa/myproject/issues/23 --field "Status" --value "In Progress"

  # Edit an item's text field value by node ID (machine / scripted use)
  $ gh project item-edit --id <item-id> --field-id <field-id> --project-id <project-id> --text "new text"

  # Clear an item's field value by node ID
  $ gh project item-edit --id <item-id> --field-id <field-id> --project-id <project-id> --clear
