// swift-tools-version: 6.2
import PackageDescription

let package = Package(
    name: "__EXEC__",
    platforms: [.macOS("__MIN_MACOS__")],
    targets: [
        .target(name: "__EXEC__Core"),
        .executableTarget(name: "__EXEC__", dependencies: ["__EXEC__Core"]),
        .testTarget(name: "__EXEC__CoreTests", dependencies: ["__EXEC__Core"]),
    ],
    swiftLanguageModes: [.v6]
)
