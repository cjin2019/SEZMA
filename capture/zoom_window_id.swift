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

print(getZoomMeetingWindowId())
