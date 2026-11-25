#!/bin/sh
# Prints a one-item Sparkle appcast. The notes file is Markdown, which Sparkle's window shows as text.
# Usage: bash Scripts/appcast.sh <CFBundleVersion> <short version> <DMG URL> <sign_update output> <notes file>
set -e
cat <<XML
<?xml version="1.0" encoding="utf-8"?>
<rss version="2.0" xmlns:sparkle="http://www.andymatuschak.org/xml-namespaces/sparkle">
  <channel>
    <title>__APP_NAME__</title>
    <item>
      <title>__APP_NAME__ $2</title>
      <pubDate>$(date -R)</pubDate>
      <sparkle:version>$1</sparkle:version>
      <sparkle:shortVersionString>$2</sparkle:shortVersionString>
      <sparkle:minimumSystemVersion>__MIN_MACOS__</sparkle:minimumSystemVersion>
      <description sparkle:format="markdown"><![CDATA[
$(cat "$5")
]]></description>
      <enclosure url="$3" $4 type="application/octet-stream"/>
    </item>
  </channel>
</rss>
XML
