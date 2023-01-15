import Cocoa
import CoreGraphics
func zoomIsReady() -> Bool {
    // Get the app that currently has the focus.
    let frontApp = NSWorkspace.shared.frontmostApplication!
    // Check if the front most app is Zoom
    if frontApp.bundleIdentifier!.contains("zoom") {
        // If it is Zoom, it still does not mean, that is receiving key events
        // (i.e., has a window at the front).
        // But what we can safely say is, that if Zoom is the front most app
        // and it has at least one window, it has to be the window that
        // crrently receives key events.
        let zoomPID = frontApp.processIdentifier

        // With this procedure, we get all available windows.
        let options = CGWindowListOption(arrayLiteral: CGWindowListOption.excludeDesktopElements, CGWindowListOption.optionOnScreenOnly)
        let windowListInfo = CGWindowListCopyWindowInfo(options, CGWindowID(0))
        let windowInfoList = windowListInfo as NSArray? as? [[String: AnyObject]]

        // Now that we have all available windows, we are going to check if at least one of them
        // is owned by Safari.
        var output = false
        var maxWidth = -1.0
        var maxHeight = -1.0
        var maxX = -1.0
        var maxY = -1.0

        for info in windowInfoList! {
            let windowPID = info["kCGWindowOwnerPID"] as! UInt32
            if  windowPID == zoomPID {
                if let bounds = info["kCGWindowBounds"] as? NSDictionary {

                    if 
                        let x = bounds["X"] as? Double,
                        let y = bounds["Y"] as? Double,
                        let width = bounds["Width"] as? Double,
                        let height = bounds["Height"] as? Double
                    {
                        if(width >= maxWidth && height >= maxHeight){
                            maxWidth = width
                            maxHeight = height
                            maxX = x
                            maxY = y
                        }
                    }
                }
                output = true
            }
        }

        let screenSize = NSScreen.main?.frame.size ?? CGSize(width: 800, height: 600)
        
        if(output){
            print("ScreenWidth: \(screenSize.width)")
            print("ScreenHeight: \(screenSize.height)")
            print ("X: \(maxX)")
            print ("Y: \(maxY)")
            print ("Width: \(maxWidth)")
            print ("Height: \(maxHeight)")
        }

        // for now ensure that zoom is full screen
        return output
    }

    return false
}

print(zoomIsReady())
