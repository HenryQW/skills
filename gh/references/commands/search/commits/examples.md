# Examples

  # Search commits matching set of keywords "readme" and "typo"
  $ gh search commits readme typo

  # Search commits matching phrase "bug fix"
  $ gh search commits "bug fix"

  # Search commits using raw search qualifiers as separate arguments
  $ gh search commits fix author:monalisa merge:false

  # Search commits committed by user "monalisa"
  $ gh search commits --committer=monalisa

  # Search commits authored by users with name "Jane Doe"
  $ gh search commits --author-name="Jane Doe"

  # Search commits matching hash "8dd03144ffdc6c0d486d6b705f9c7fba871ee7c3"
  $ gh search commits --hash=8dd03144ffdc6c0d486d6b705f9c7fba871ee7c3

  # Search commits authored before February 1st, 2022
  $ gh search commits --author-date="<2022-02-01"
