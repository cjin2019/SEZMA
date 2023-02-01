import Cocoa
import CoreGraphics

struct CapturedFrame {
    var content: CIImage
    var filename: String
}

func writeFirstFrameInBufferToFile(buffer: [CapturedFrame], ciContext: CIContext) throws{
    var frame: CapturedFrame = buffer.removeFirst()
    try ciContext.writeJPEGRepresentation(of: frame.content, to: URL(string: frame.filename)!, colorSpace: frame.content.colorSpace!)
}

func saveCGIImages(windowIdParam: Int, imageDirectory: String, durationSeconds: Double) async throws{

    let ciContext: CIContext = CIContext()
    let formatter = DateFormatter()
    formatter.dateFormat = "yyyy.MM.dd.HH.mm.ss.SSS"
    let startTime: TimeInterval = Date().timeIntervalSinceReferenceDate
    let timeBetweenFrame = 0.033  // in seconds

    var buffer: [CapturedFrame] = []
    let bufferSize: Int = 6;
    let queue: DispatchQueue = DispatchQueue(label: "thread-safe-array")

    await withTaskGroup(of: Never.self,
                returning: Never.self, 
                body: { taskGroup in
        
        // capture frames
        taskGroup.addTask {
            while Date().timeIntervalSinceReferenceDate - startTime <= durationSeconds {
                queue.as
                if (buffer.count == bufferSize){
                    continue
                }
                let time: TimeInterval = Date().timeIntervalSinceReferenceDate
                let image: CGImage = CGWindowListCreateImage(CGRectNull, CGWindowListOption.optionIncludingWindow, CGWindowID(windowIdParam), CGWindowImageOption.boundsIgnoreFraming)!
                let ciImage: CIImage = CIImage(cgImage: image)
                let imageFilePath: String = "file://\(imageDirectory)/\(formatter.string(from: Date(timeIntervalSinceReferenceDate: time))).jpg"

                queue.async {
                    buffer.append(CapturedFrame(content: ciImage, filename: imageFilePath))
                }

                // buffer.append(CapturedFrame(content: ciImage, filename: imageFilePath))
                let time2: TimeInterval = Date().timeIntervalSinceReferenceDate
                if (timeBetweenFrame - (time2 - time) > 0){
                    usleep(useconds_t(max(0, (timeBetweenFrame - (time2 - time)) * 1000000)))
                }
            }
        }

        // write images to file
        taskGroup.addTask{
            while Date().timeIntervalSinceReferenceDate - startTime <= durationSeconds {
                queue.async {
                    do {
                        if (buffer.count > 0){
                            writeFirstFrameInBufferToFile(buffer: buffer, ciContext: ciContext)
                        }  
                    } catch error {
                        throw error
                    }
                     
                }
            }

            // in case there are left over images from the buffer
            queue.async {
                while buffer.count > 0 {
                    writeFirstFrameInBufferToFile(buffer: buffer, ciContext: ciContext)
                }
            }
        }
                
    })

    // while Date().timeIntervalSinceReferenceDate - startTime <= durationSeconds {
    //     let time: TimeInterval = Date().timeIntervalSinceReferenceDate
    //     let image: CGImage = CGWindowListCreateImage(CGRectNull, CGWindowListOption.optionIncludingWindow, CGWindowID(windowIdParam), CGWindowImageOption.boundsIgnoreFraming)!
    //     let ciImage: CIImage = CIImage(cgImage: image)
    //     let imageFilePath: String = "file://\(imageDirectory)/\(formatter.string(from: Date(timeIntervalSinceReferenceDate: time))).jpg"
    //     try ciContext.writeJPEGRepresentation(of: ciImage, to: URL(string: imageFilePath)!, colorSpace: ciImage.colorSpace!)
    //     let time2: TimeInterval = Date().timeIntervalSinceReferenceDate
    //     if (timeBetweenFrame - (time2 - time) > 0){
    //         usleep(useconds_t(max(0, (timeBetweenFrame - (time2 - time)) * 1000000)))
    //     }
        
    // }

}

let windowIdParam: Int = Int(CommandLine.arguments[1])!
let imageDirectory: String = CommandLine.arguments[2]
let durationSeconds: Double = Double(CommandLine.arguments[3])!
try await saveCGIImages(windowIdParam: windowIdParam, imageDirectory: imageDirectory, durationSeconds: durationSeconds)