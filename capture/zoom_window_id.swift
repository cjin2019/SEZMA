import Cocoa
import CoreGraphics

func getZoomMeetingWindowId() -> Int{
    // With this procedure, we get all available windows.
    let options = CGWindowListOption(arrayLiteral: CGWindowListOption.excludeDesktopElements, CGWindowListOption.optionOnScreenOnly)
    let windowListInfo = CGWindowListCopyWindowInfo(options, CGWindowID(0))
    let windowInfoList = windowListInfo as NSArray? as? [[String: AnyObject]]

    for info in windowInfoList! {
        let windowNum = info["kCGWindowNumber"] as! Int
        let ownerName = info["kCGWindowOwnerName"] as! String
        let windowName = info["kCGWindowName"] as! String

        if ownerName == "zoom.us" && windowName == "Zoom Meeting" {
            return windowNum
        }

        // print("WindowNumber: \(windowNum), WindowOwnername: \(ownerName), WindowName: \(windowName)")
    }

    return -1

}

func saveCGIImage(windowIdParam: Int) throws{
    var filePaths: [String] = []
    var images: [CIImage] = []
    var count: Int = 0

    let ciContext: CIContext = CIContext()
    let timeBetweenFrames = 0.033
    let formatter = DateFormatter()
    formatter.dateFormat = "yyyy-MM-dd'T'HH:mm:ss.SSS"
    
    while count < 100 {
        let imageTimeInterval: TimeInterval = Date().timeIntervalSince1970
        let timeStr: String = formatter.string(from: Date(timeIntervalSince1970: imageTimeInterval))
        let image: CGImage = CGWindowListCreateImage(CGRectInfinite, CGWindowListOption.optionIncludingWindow, CGWindowID(windowIdParam), CGWindowImageOption.boundsIgnoreFraming)!
        let ciImage: CIImage = CIImage(cgImage: image)
        let imageFilePath: String = "/Users/carolinejin/Documents/meng_project/data/test_screencapture/\(timeStr).png"
        
        filePaths.append(imageFilePath)
        images.append(ciImage)
        count += 1
        
        let timeToSleep = (timeBetweenFrames - (Date().timeIntervalSince1970 - imageTimeInterval)) * 1000000
        if(timeToSleep > 0){
            usleep(UInt32(timeToSleep))
        }
        // try ciContext.writePNGRepresentation(of: ciImage, to: URL(filePath: imageFilePath), format: .BGRA8, colorSpace: ciImage.colorSpace!)
    }

    for (imageFilePath, ciImage) in zip(filePaths, images){
        try ciContext.writePNGRepresentation(of: ciImage, to: URL(filePath: imageFilePath), format: .BGRA8, colorSpace: ciImage.colorSpace!)
    }

    // let formatter = DateFormatter()
    // formatter.dateFormat = "yyyy-MM-dd'T'HH:mm:ss.SSS"
    // for time: TimeInterval in times {
    //     print()
    // }

    // var idx = 0
    // for image: CGImage in images {
        
    //     let ciImage: CIImage = CIImage(cgImage: image)
    //     let imageFilePath: String = "/Users/carolinejin/Documents/meng_project/data/test_screencapture/\(idx).png"
    //     try ciContext.writePNGRepresentation(of: ciImage, to: URL(filePath: imageFilePath), format: .BGRA8, colorSpace: ciImage.colorSpace!)
    //     idx += 1
    // }
}

try saveCGIImage(windowIdParam: getZoomMeetingWindowId())
// print(getZoomMeetingWindowId())
// int main(int argc, char **argv)
// {
//    NSArray *windows = (NSArray *)CGWindowListCopyWindowInfo(kCGWindowListExcludeDesktopElements|kCGWindowListOptionOnScreenOnly,kCGNullWindowID);
//    for(NSDictionary *window in windows){
//       int WindowNum = [[window objectForKey:(NSString *)kCGWindowNumber] intValue];
//       NSString* OwnerName = [window objectForKey:(NSString *)kCGWindowOwnerName];
//       NSString* WindowName= [window objectForKey:(NSString *)kCGWindowName];
//       printf("%s:%s:%d\n",[OwnerName UTF8String],[WindowName UTF8String],WindowNum);
//    }
// }