# AirQR iOS App

Native receiver/sender using AVFoundation + Vision + SwiftUI.

## Why native
- Vision barcode detection at 10-30 fps vs web fallback
- Better focus/exposure control, low-light
- Save to Files/Downloads, share sheet

## Build
1. Open Xcode 15+, create App project, add `mobile/ios/Sources/AirQR/*.swift`.
2. Add `NSCameraUsageDescription` to Info.plist.
3. Run on device (camera required; Simulator cannot scan).

## Sender params UI
Chunk size, frame interval, QR size fields with live chunk-count preview (see `ContentView`).
