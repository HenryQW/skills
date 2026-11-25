.PHONY: build test clean cert app dev-app run-dev install-app run-app

APP_NAME := __APP_NAME__
APP_ID := __BUNDLE_ID__
# The app's own identity (`make cert`, signing.md) keeps macOS permissions across builds. Without it, sign ad hoc ("-").
IDENTITY ?= $(shell security find-identity -p codesigning | grep -qF '"$(APP_NAME) Self-Signed"' && echo "$(APP_NAME) Self-Signed" || echo -)
APP := .build/$(APP_NAME).app
DEV_APP := .build/$(APP_NAME) Dev.app
DEV_ID := $(APP_ID).dev
TESTING_PLUGINS := /Library/Developer/CommandLineTools/usr/lib/swift/host/plugins/testing

build:
	swift build -c release

# Command Line Tools: swift test does not find the Swift Testing macros without this plugin path.
test:
	swift test -Xswiftc -plugin-path -Xswiftc $(TESTING_PLUGINS)

clean:
	swift package clean

cert:
	Scripts/make-cert.sh

app:
	IDENTITY="$(IDENTITY)" sh Scripts/bundle.sh --local

# A dev build with its own identity and name, for checks while the installed app runs.
dev-app: app
	rm -rf "$(DEV_APP)"
	ditto "$(APP)" "$(DEV_APP)"
	plutil -replace CFBundleIdentifier -string $(DEV_ID) "$(DEV_APP)/Contents/Info.plist"
	plutil -replace CFBundleName -string "$(APP_NAME) Dev" "$(DEV_APP)/Contents/Info.plist"
	plutil -replace CFBundleDisplayName -string "$(APP_NAME) Dev" "$(DEV_APP)/Contents/Info.plist"
	codesign --force --preserve-metadata=flags --timestamp=none -s "$(IDENTITY)" -i $(DEV_ID) "$(DEV_APP)"

# One dev build at a time on this Mac: waits for the others, runs until the app quits, then unregisters it.
run-dev: dev-app
	Scripts/run-dev.sh "$(CURDIR)/$(DEV_APP)"

install-app: app
	sh Scripts/install-app.sh "$(APP)" /Applications

run-app: install-app
	open "/Applications/$(APP_NAME).app"
