import SwiftUI
import AVFoundation
import Vision

struct ScannerView: UIViewControllerRepresentable {
    @ObservedObject var session: TransferSession
    func makeUIViewController(context: Context) -> VC { VC(session: session) }
    func updateUIViewController(_ uiViewController: VC, context: Context) {}
    class VC: UIViewController, AVCaptureVideoDataOutputSampleBufferDelegate {
        let session: TransferSession
        let cap = AVCaptureSession()
        init(session: TransferSession) { self.session = session; super.init(nibName: nil, bundle: nil) }
        required init?(coder: NSCoder) { fatalError() }
        override func viewDidLoad() {
            super.viewDidLoad()
            guard let dev = AVCaptureDevice.default(.builtInWideAngleCamera, for: .video, position: .back),
                  let inp = try? AVCaptureDeviceInput(device: dev) else { return }
            cap.addInput(inp)
            let out = AVCaptureVideoDataOutput()
            out.setSampleBufferDelegate(self, queue: .global())
            cap.addOutput(out)
            let layer = AVCaptureVideoPreviewLayer(session: cap)
            layer.frame = view.bounds; layer.videoGravity = .resizeAspectFill
            view.layer.addSublayer(layer)
            cap.startRunning()
        }
        func captureOutput(_ output: AVCaptureOutput, didOutput sb: CMSampleBuffer, from conn: AVCaptureConnection) {
            guard let px = CMSampleBufferGetImageBuffer(sb) else { return }
            let req = VNDetectBarcodesSymbologiesRequest { r, _ in
                for o in (r.results as? [VNBarcodeObservation] ?? []) {
                    if let s = o.payloadStringValue { DispatchQueue.main.async { self.session.feed(s) } }
                }
            }
            req.symbologies = [.qr]
            try? VNImageRequestHandler(cvPixelBuffer: px).perform([req])
        }
    }
}

struct ContentView: View {
    @StateObject var session = TransferSession()
    @State var chunkSize = "800"
    @State var frameMs = "1200"
    @State var qrSize = "280"
    var body: some View {
        TabView {
            VStack {
                Text("AirQR Native Receiver (Vision)").font(.headline)
                ScannerView(session: session)
                Text(session.status).font(.caption).monospaced()
                Text(session.progress).font(.caption).monospaced()
            }.tabItem { Text("Receive") }
            VStack {
                Text("AirQR Native Sender").font(.headline)
                TextField("Chunk size (200-2000)", text: $chunkSize).textFieldStyle(.roundedBorder)
                TextField("Frame interval ms", text: $frameMs).textFieldStyle(.roundedBorder)
                TextField("QR size px", text: $qrSize).textFieldStyle(.roundedBorder)
                Text("Chunks preview: file size / chunk size = chunk count. Total frames = data + manifest + done.").font(.caption)
                Text("Pick files via Files app, then present QRs. Params apply live.").font(.caption)
            }.tabItem { Text("Send") }
        }
    }
}
