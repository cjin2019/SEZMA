import Cocoa
import CoreGraphics

func saveCGIImages(windowIdParam: Int, imageDirectory: String, durationSeconds: Double) throws{

    
    let ciContext: CIContext = CIContext()
    let formatter = DateFormatter()
    formatter.dateFormat = "yyyy.MM.dd.HH.mm.ss.SSS"
    let startTime: TimeInterval = Date().timeIntervalSinceReferenceDate
    let timeBetweenFrame = 0.033  // in seconds

    while Date().timeIntervalSinceReferenceDate - startTime <= durationSeconds {
        let time: TimeInterval = Date().timeIntervalSinceReferenceDate
        let image: CGImage = CGWindowListCreateImage(CGRectNull, CGWindowListOption.optionIncludingWindow, CGWindowID(windowIdParam), CGWindowImageOption.boundsIgnoreFraming)!
        let ciImage: CIImage = CIImage(cgImage: image)
        let imageFilePath: String = "\(imageDirectory)/\(formatter.string(from: Date(timeIntervalSinceReferenceDate: time))).jpg"
        try ciContext.writeJPEGRepresentation(of: ciImage, to: URL(filePath: imageFilePath), colorSpace: ciImage.colorSpace!)
        let time2: TimeInterval = Date().timeIntervalSinceReferenceDate
        if (timeBetweenFrame - (time2 - time) > 0){
            usleep(useconds_t(max(0, (timeBetweenFrame - (time2 - time)) * 1000000)))
        }
        
    }

}

let windowIdParam: Int = Int(CommandLine.arguments[1])!
let imageDirectory: String = CommandLine.arguments[2]
let durationSeconds: Double = Double(CommandLine.arguments[3])!
try saveCGIImages(windowIdParam: windowIdParam, imageDirectory: imageDirectory, durationSeconds: durationSeconds)