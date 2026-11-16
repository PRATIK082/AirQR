// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "AirQR",
    platforms: [.iOS(.v17)],
    products: [.library(name: "AirQR", targets: ["AirQR"])],
    targets: [.target(name: "AirQR", path: "Sources/AirQR")]
)
