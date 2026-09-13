# Examples

  # Create a field in the current user's project "1"
  $ gh project field-create 1 --owner "@me" --name "new field" --data-type "text"

  # Create a field with three options to select from for owner monalisa
  $ gh project field-create 1 --owner monalisa --name "new field" --data-type "SINGLE_SELECT" --single-select-options "one,two,three"
