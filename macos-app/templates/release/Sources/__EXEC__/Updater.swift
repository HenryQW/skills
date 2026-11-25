import AppKit
import Observation
import Sparkle

// Needs, in Package.swift: .package(url: "https://github.com/sparkle-project/Sparkle", exact: "<version>"), the
// product "Sparkle" on the app target, and linkerSettings: [.unsafeFlags(["-Xlinker", "-rpath", "-Xlinker",
// "@executable_path/../Frameworks"])] (Scripts/bundle.sh puts Sparkle.framework there).
// Needs, in Packaging/Info.plist: SUFeedURL = https://github.com/__GH_REPO__/releases/latest/download/appcast.xml,
// SUPublicEDKey = the public EdDSA key, SUEnableAutomaticChecks = true.

/// Updates through Sparkle: it reads the appcast of the chosen channel once a day and shows its own window for a new
/// version. An update must carry an EdDSA signature from the app's key (`SUPublicEDKey`).
@MainActor @Observable
final class Updater {
    enum Channel: String, CaseIterable { case stable, beta }

    static let shared = Updater()
    @ObservationIgnored private let controller: SPUStandardUpdaterController
    /// Sparkle keeps a weak reference to its delegate.
    @ObservationIgnored private let feed: Feed

    /// Check for updates automatically; Sparkle keeps it in the user defaults.
    var automaticChecks: Bool {
        didSet { controller.updater.automaticallyChecksForUpdates = automaticChecks }
    }
    /// Download a new version and install it when the app quits; Sparkle keeps it in the user defaults.
    var automaticInstall: Bool {
        didSet { controller.updater.automaticallyDownloadsUpdates = automaticInstall }
    }
    /// Stable: the latest GitHub release (`SUFeedURL`). Beta: the `beta` prerelease, a build of each push to main.
    var channel: Channel {
        didSet {
            UserDefaults.standard.set(channel.rawValue, forKey: "updateChannel")
            feed.beta = channel == .beta
        }
    }

    private init() {
        let channel = UserDefaults.standard.string(forKey: "updateChannel").flatMap(Channel.init) ?? .stable
        self.channel = channel
        let feed = Feed(beta: channel == .beta)
        self.feed = feed
        controller = SPUStandardUpdaterController(startingUpdater: false, updaterDelegate: feed, userDriverDelegate: nil)
        automaticChecks = controller.updater.automaticallyChecksForUpdates
        automaticInstall = controller.updater.automaticallyDownloadsUpdates
    }

    func start() {
        controller.startUpdater()
    }

    /// Check for Updates…: the app comes to the front for Sparkle's window.
    func check() {
        NSApp.activate(ignoringOtherApps: true)
        controller.checkForUpdates(nil)
    }

    /// Gives Sparkle the beta feed in place of `SUFeedURL`. Sparkle never installs an older version, so a beta stays
    /// until a release is newer.
    private final class Feed: NSObject, SPUUpdaterDelegate {
        var beta: Bool

        init(beta: Bool) { self.beta = beta }

        func feedURLString(for updater: SPUUpdater) -> String? {
            beta ? "https://github.com/__GH_REPO__/releases/download/beta/appcast.xml" : nil
        }
    }
}
