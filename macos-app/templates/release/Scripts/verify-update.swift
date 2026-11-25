// Checks a Sparkle update before a workflow publishes it, as each installed copy will: the EdDSA signature in the
// appcast against the archive (__EXEC__.dmg) and the independently pinned public key, the archive's length, and the appcast version
// against the app's CFBundleVersion. A wrong or missing key would strand every installed copy, so a mismatch fails.
// Usage: swift Scripts/verify-update.swift <__APP_NAME__.app> <archive> <appcast.xml> <pinned-public-key>
import CryptoKit
import Foundation

func fail(_ message: String) -> Never {
    FileHandle.standardError.write(Data("verify-update: \(message)\n".utf8))
    exit(1)
}

let args = CommandLine.arguments
guard args.count == 5 else { fail("usage: verify-update.swift <app> <archive> <appcast.xml> <pinned-public-key>") }
let info = NSDictionary(contentsOf: URL(fileURLWithPath: args[1]).appending(path: "Contents/Info.plist")) as? [String: Any] ?? [:]
guard let key = Data(base64Encoded: args[4]),
      let publicKey = try? Curve25519.Signing.PublicKey(rawRepresentation: key) else { fail("invalid pinned public key") }
guard let candidate = info["SUPublicEDKey"] as? String, Data(base64Encoded: candidate) == key else {
    fail("the candidate app has a different public key from the release pin")
}
guard let archive = FileManager.default.contents(atPath: args[2]) else { fail("cannot read \(args[2])") }
guard let appcast = try? XMLDocument(contentsOf: URL(fileURLWithPath: args[3])),
      let item = try? appcast.nodes(forXPath: "//item").first as? XMLElement,
      let enclosure = item.elements(forName: "enclosure").first else { fail("no item with an enclosure in the appcast") }
let ns = "http://www.andymatuschak.org/xml-namespaces/sparkle"
guard let signature = enclosure.attribute(forLocalName: "edSignature", uri: ns)?.stringValue.flatMap({ Data(base64Encoded: $0) }) else {
    fail("no sparkle:edSignature on the enclosure")
}
guard publicKey.isValidSignature(signature, for: archive) else { fail("the signature does not match SUPublicEDKey") }
guard enclosure.attribute(forName: "length")?.stringValue == String(archive.count) else { fail("the enclosure length is not the archive's size") }
let version = item.elements(forLocalName: "version", uri: ns).first?.stringValue
guard let version, !version.isEmpty, version == info["CFBundleVersion"] as? String else { fail("sparkle:version \(version ?? "none") is not the app's CFBundleVersion") }
print("verify-update: the update is signed with SUPublicEDKey, version \(version)")
