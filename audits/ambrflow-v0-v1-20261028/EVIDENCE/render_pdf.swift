import Foundation
import PDFKit
import AppKit
let url = URL(fileURLWithPath: CommandLine.arguments[1])
let doc = PDFDocument(url: url)!
let page = doc.page(at: Int(CommandLine.arguments[2])!)!
let size = page.bounds(for: .mediaBox).size
let img = page.thumbnail(of: NSSize(width:size.width*3, height:size.height*3), for: .mediaBox)
let tiff = img.tiffRepresentation!
let rep = NSBitmapImageRep(data: tiff)!
try! rep.representation(using: .png, properties: [:])!.write(to: URL(fileURLWithPath: CommandLine.arguments[3]))
