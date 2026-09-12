# Details

## Description

GitHub CLI extensions are repositories that provide additional gh commands.

The name of the extension repository must start with `gh-` and it must contain an
executable of the same name. All arguments passed to the `gh <extname>` invocation
will be forwarded to the `gh-<extname>` executable of the extension.

An extension cannot override any of the core gh commands. If an extension name conflicts
with a core gh command, you can use `gh extension exec <extname>`.

When an extension is executed, gh will check for new versions once every 24 hours and display
an upgrade notice. See `gh help environment` for information on disabling extension notices.

Extensions are not verified, signed, or endorsed by GitHub. When you install or upgrade
		an extension, you are trusting its publisher. It is your responsibility to review the
		source and provenance of any extension before use.

For the list of available extensions, see <https://github.com/topics/gh-extension>.
