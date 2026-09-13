# Examples

  $ gh codespace cp -e README.md 'remote:/workspaces/$RepositoryName/'
  $ gh codespace cp -e 'remote:~/*.go' ./gofiles/
  $ gh codespace cp -e 'remote:/workspaces/myproj/go.{mod,sum}' ./gofiles/
  $ gh codespace cp -e -- -F ~/.ssh/codespaces_config 'remote:~/*.go' ./gofiles/
