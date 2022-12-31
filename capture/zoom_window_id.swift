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