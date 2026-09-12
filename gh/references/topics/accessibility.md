Learn about GitHub CLI's accessibility experiences

As the home for all developers, we want every developer to feel welcome in our
community and be empowered to contribute to the future of global software
development with everything GitHub has to offer including the GitHub CLI.

Customizable and contrasting colors

Text interfaces often use color for various purposes, but insufficient contrast
or customizability can leave some users unable to benefit.

For a more accessible experience, the GitHub CLI can use color palettes
based on terminal background appearance and limit colors to 4-bit ANSI color
palettes, which users can customize within terminal preferences.

With this new experience, the GitHub CLI provides multiple options to address
color usage:

1. The GitHub CLI will use 4-bit color palette for increased color contrast based
   on dark and light backgrounds including rendering Markdown based on the
   GitHub Primer design system.

   To enable this experience, use one of the following methods:
   - Run `gh config set accessible_colors enabled`
   - Set `GH_ACCESSIBLE_COLORS=enabled` environment variable

2. The GitHub CLI will display issue and pull request labels' custom RGB colors
   in terminals with true color support.

   To enable this experience, use one of the following methods:
   - Run `gh config set color_labels enabled`
   - Set `GH_COLOR_LABELS=enabled` environment variable

Non-interactive user input prompting

Interactive text user interfaces manipulate the terminal cursor to redraw parts
of the screen, which can be difficult for speech synthesizers or braille displays
to accurately detect and read.

For a more accessible experience, the GitHub CLI can provide a similar experience using
non-interactive prompts for user input.

To enable this experience, use one of the following methods:
- Run `gh config set accessible_prompter enabled`
- Set `GH_ACCESSIBLE_PROMPTER=enabled` environment variable

Text-based spinners

Motion-based spinners communicate in-progress activity by manipulating the
terminal cursor to create a spinning effect, which may cause discomfort to users
with motion sensitivity or miscommunicate information to speech synthesizers.

For a more accessible experience, this interactivity can be disabled in favor
of text-based progress indicators.

To enable this experience, use one of the following methods:
- Run `gh config set spinner disabled`
- Set `GH_SPINNER_DISABLED=yes` environment variable

Join the conversation

We invite you to join us in improving GitHub CLI accessibility by sharing your
feedback and ideas through GitHub Accessibility feedback channels:

https://github.com/orgs/community/discussions/categories/accessibility


USAGE
  gh accessibility [flags]

ALIASES
  gh a11y

FLAGS
  -w, --web   Open the GitHub Accessibility site in your browser

INHERITED FLAGS
  --help   Show help for command

EXAMPLES
  # Open the GitHub Accessibility site in your browser
  $ gh accessibility --web

  # Display color using customizable, 4-bit accessible colors
  $ gh config set accessible_colors enabled

  # Use input prompts without redrawing the screen
  $ gh config set accessible_prompter enabled

  # Disable motion-based spinners for progress indicators in favor of text
  $ gh config set spinner disabled

LEARN MORE
  Use `gh <command> <subcommand> --help` for more information about a command.
  Read the manual at https://cli.github.com/manual
  Learn about exit codes using `gh help exit-codes`
  Learn about accessibility experiences using `gh help accessibility`
