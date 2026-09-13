# Examples

  # Download all assets from a specific release
  $ gh release download v1.2.3

  # Download only Debian packages for the latest release
  $ gh release download --pattern '*.deb'

  # Specify multiple file patterns
  $ gh release download -p '*.deb' -p '*.rpm'

  # Download the archive of the source code for a release
  $ gh release download v1.2.3 --archive=zip
