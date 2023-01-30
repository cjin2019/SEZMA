import ScreenCaptureKit

// Following https://developer.apple.com/documentation/screencapturekit/capturing_screen_content_in_macos

enum ZoomScreenCaptureError: Error {
    case failedGettingZoomWindow(errorMsg: String)
}

func getZoomWindow() async throws -> SCWindow? {
    do {
        let availableContent = try await SCShareableContent.excludingDesktopWindows(false, onScreenWindowsOnly: true)

        for window in availableContent.windows {
            if(window.title == "Zoom Meeting"){
                return window;
            }
        }
    } catch {
        // to-do logging
        let errMsg = "Failed to get the shareable content: \(error.localizedDescription)"
        throw ZoomScreenCaptureError.failedGettingZoomWindow(errorMsg: errMsg)
    }

    return nil
}

func configCapture(window: SCWindow) -> (SCContentFilter, SCStreamConfiguration){
    let filter = SCContentFilter(desktopIndependentWindow: window)

    let streamConfig = SCStreamConfiguration()
    
    // configure display content and width
    streamConfig.width = Int(window.frame.width) + 10
    streamConfig.height = Int(window.frame.height) + 10

    // configure the capture interval at 30 fps (https://support.zoom.us/hc/en-us/articles/202920719-Accessing-meeting-and-phone-statistics)
    streamConfig.minimumFrameInterval = CMTime(value: 1, timescale: 30)

    // Increase the depth of the frame queue to ensure high fps at the expense of increasing
    // the memory footprint of WindowServer.
    streamConfig.queueDepth = 5

    return (filter, streamConfig)
    
}

func capture(filter: SCContentFilter, streamConfig: SCStreamConfiguration, durationSeconds: Float64, outputFile: String){
    let stream = SCStream(filter: filter, configuration: streamConfig)
}

let window = try await getZoomWindow()!
print(configCapture(window: window))
