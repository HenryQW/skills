# Examples

  # List releases in the current repository
  $ gh api repos/{owner}/{repo}/releases

  # Post an issue comment
  $ gh api repos/{owner}/{repo}/issues/123/comments -f body='Hi from CLI'

  # Post nested parameter read from a file
  $ gh api gists -F 'files[myfile.txt][content]=@myfile.txt'

  # Add parameters to a GET request
  $ gh api -X GET search/issues -f q='repo:cli/cli is:open remote'

  # Use a JSON file as request body
  $ gh api repos/{owner}/{repo}/rulesets --input file.json

  # Set a custom HTTP header
  $ gh api -H 'Accept: application/vnd.github.v3.raw+json' ...

  # Opt into GitHub API previews
  $ gh api --preview baptiste,nebula ...

  # Print only specific fields from the response
  $ gh api repos/{owner}/{repo}/issues --jq '.[].title'

  # Use a template for the output
  $ gh api repos/{owner}/{repo}/issues --template \
    '{{range .}}{{.title}} ({{.labels | pluck "name" | join ", " | color "yellow"}}){{"\n"}}{{end}}'

  # Update allowed values of the "environment" custom property in a deeply nested array
  $ gh api -X PATCH /orgs/{org}/properties/schema \
     -F 'properties[][property_name]=environment' \
     -F 'properties[][default_value]=production' \
     -F 'properties[][allowed_values][]=staging' \
     -F 'properties[][allowed_values][]=production'

  # List releases with GraphQL
  $ gh api graphql -F owner='{owner}' -F name='{repo}' -f query='
    query($name: String!, $owner: String!) {
      repository(owner: $owner, name: $name) {
        releases(last: 3) {
          nodes { tagName }
        }
      }
    }
  '

  # List all repositories for a user
  $ gh api graphql --paginate -f query='
    query($endCursor: String) {
      viewer {
        repositories(first: 100, after: $endCursor) {
          nodes { nameWithOwner }
          pageInfo {
            hasNextPage
            endCursor
          }
        }
      }
    }
  '

  # Get the percentage of forks for the current user
  $ gh api graphql --paginate --slurp -f query='
    query($endCursor: String) {
      viewer {
        repositories(first: 100, after: $endCursor) {
          nodes { isFork }
          pageInfo {
            hasNextPage
            endCursor
          }
        }
      }
    }
  ' | jq 'def count(e): reduce e as $_ (0;.+1);
  [.[].data.viewer.repositories.nodes[]] as $r | count(select($r[].isFork))/count($r[])'
