import Cocoa
import CoreGraphics

func saveCGIImages(windowIdParam: Int, imageDirectory: String, durationSeconds: Double) throws{

    
    let ciContext: CIContext = CIContext()
    let formatter = DateFormatter()
    formatter.dateFormat = "yyyy.MM.dd.HH.mm.ss.SSS"
    let startTime: TimeInterval = Date().timeIntervalSince1970

    while Date().timeIntervalSince1970 - startTime <= durationSeconds {
        // let timeStr: String = formatter.string(from: Date(timeIntervalSince1970: imageTimeInterval))
        let image: CGImage = CGWindowListCreateImage(CGRectNull, CGWindowListOption.optionIncludingWindow, CGWindowID(windowIdParam), CGWindowImageOption.boundsIgnoreFraming)!
        let ciImage: CIImage = CIImage(cgImage: image)
        let imageFilePath: String = "\(imageDirectory)/\(formatter.string(from: Date(timeIntervalSince1970: Date().timeIntervalSince1970))).jpg"
        try ciContext.writeJPEGRepresentation(of: ciImage, to: URL(filePath: imageFilePath), colorSpace: ciImage.colorSpace!)
    }

}

let windowIdParam: Int = Int(CommandLine.arguments[1])!
let imageDirectory: String = CommandLine.arguments[2]
let durationSeconds: Double = Double(CommandLine.arguments[3])!
try saveCGIImages(windowIdParam: windowIdParam, imageDirectory: imageDirectory, durationSeconds: durationSeconds)