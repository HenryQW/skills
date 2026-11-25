// Render Packaging/AppIcon.icns and website/public/icon.png on Apple's 1024 px grid: swift Scripts/make-icon.swift
// Run it from the repo root. Edit only drawMark and the two colours.
import CoreGraphics
import Foundation
import ImageIO
import UniformTypeIdentifiers

func rgb(_ hex: Int, _ alpha: CGFloat = 1) -> CGColor {
    CGColor(red: CGFloat(hex >> 16) / 255, green: CGFloat(hex >> 8 & 0xFF) / 255, blue: CGFloat(hex & 0xFF) / 255, alpha: alpha)
}

/// TODO: draw the app's mark here. The context is the 120 pt tile with the y axis down.
/// `small` is true at 16 and 32 px: use thicker strokes and fewer details.
/// This placeholder is a white circle. Replace it.
func drawMark(_ ctx: CGContext, small: Bool) {
    ctx.setFillColor(rgb(0xFFFFFF))
    ctx.fillEllipse(in: CGRect(x: 30, y: 30, width: 60, height: 60))
}

/// Drawn in a 120 pt tile with the y axis down, scaled onto the 824 px body of the 1024 px grid.
func render(_ px: Int, small: Bool = false) -> Data {
    let k = CGFloat(px) / 1024
    let ctx = CGContext(data: nil, width: px, height: px, bitsPerComponent: 8, bytesPerRow: 0,
                        space: CGColorSpaceCreateDeviceRGB(), bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue)!
    ctx.translateBy(x: 100 * k, y: CGFloat(px) - 100 * k)
    ctx.scaleBy(x: 824 * k / 120, y: -824 * k / 120)
    let tile = CGPath(roundedRect: CGRect(x: 0, y: 0, width: 120, height: 120), cornerWidth: 27, cornerHeight: 27, transform: nil)
    ctx.saveGState()
    ctx.addPath(tile)
    ctx.clip()
    let gradient = CGGradient(colorsSpace: CGColorSpaceCreateDeviceRGB(), colors: [rgb(0x2A86F0), rgb(0x0A5CC4)] as CFArray, locations: [0, 1])!
    ctx.drawLinearGradient(gradient, start: .zero, end: CGPoint(x: 0, y: 120), options: [])
    ctx.restoreGState()

    drawMark(ctx, small: small)

    let data = NSMutableData()
    let dest = CGImageDestinationCreateWithData(data, UTType.png.identifier as CFString, 1, nil)!
    CGImageDestinationAddImage(dest, ctx.makeImage()!, nil)
    CGImageDestinationFinalize(dest)
    return data as Data
}

let set = FileManager.default.temporaryDirectory.appendingPathComponent("AppIcon.iconset")
try? FileManager.default.removeItem(at: set)
try FileManager.default.createDirectory(at: set, withIntermediateDirectories: true)
for size in [16, 32, 128, 256, 512] {
    try render(size, small: size <= 32).write(to: set.appendingPathComponent("icon_\(size)x\(size).png"))
    try render(size * 2, small: size == 16).write(to: set.appendingPathComponent("icon_\(size)x\(size)@2x.png"))
}
try render(512).write(to: URL(fileURLWithPath: "website/public/icon.png"))
let iconutil = Process()
iconutil.executableURL = URL(fileURLWithPath: "/usr/bin/iconutil")
iconutil.arguments = ["-c", "icns", set.path, "-o", "Packaging/AppIcon.icns"]
try iconutil.run()
iconutil.waitUntilExit()
try FileManager.default.removeItem(at: set)
exit(iconutil.terminationStatus)
