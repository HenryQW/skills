# Examples

  # Create an alphanumeric autolink to example.com for the key prefix "TICKET-".
  # Generates https://example.com/TICKET?query=123abc from "TICKET-123abc".
  $ gh repo autolink create TICKET- "https://example.com/TICKET?query=<num>"

  # Create a numeric autolink to example.com for the key prefix "STORY-".
  # Generates https://example.com/STORY?id=123 from "STORY-123".
  $ gh repo autolink create STORY- "https://example.com/STORY?id=<num>" --numeric
