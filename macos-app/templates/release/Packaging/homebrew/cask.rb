# The cask for __TAP_REPO__. The release workflow fills in the version and the SHA-256 and commits it to the tap as
# Casks/__CASK__.rb.
cask "__CASK__" do
  version "@VERSION@"
  sha256 "@SHA256@"

  url "https://github.com/__GH_REPO__/releases/download/v#{version}/__EXEC__.dmg"
  name "__APP_NAME__"
  desc "__DESC__"
  homepage "__HOMEPAGE__"

  # The app updates itself with Sparkle, so brew upgrade leaves it alone unless --greedy.
  auto_updates true
  # The runner builds for Apple silicon only. Use the Homebrew name of __MIN_MACOS__ (macOS 27 is :golden_gate).
  depends_on arch: :arm64
  depends_on macos: :golden_gate

  app "__APP_NAME__.app"

  # The app has no Developer ID, so macOS calls a quarantined copy damaged.
  postflight do
    system_command "/usr/bin/xattr", args: ["-dr", "com.apple.quarantine", "#{appdir}/__APP_NAME__.app"]
  end

  # Only the folders the app writes.
  zap trash: [
    "~/Library/Application Support/__APP_NAME__",
    "~/Library/Preferences/__BUNDLE_ID__.plist",
  ]
end
