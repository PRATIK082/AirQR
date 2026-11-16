import Foundation

public struct Flags {
    public static let manifest = 8
    public static let done = 16
    public static let parity = 64
}

public struct AirQrPacket {
    public let transferIdHex: String
    public let fileId: UInt32
    public let totalChunks: UInt32
    public let chunkIndex: UInt32
    public let payload: Data
    public let flags: UInt8

    static func crc32(_ d: Data) -> UInt32 {
        var table = [UInt32](repeating: 0, count: 256)
        for i in 0..<256 {
            var c = UInt32(i)
            for _ in 0..<8 { c = (c & 1) == 1 ? (0xEDB88320 ^ (c >> 1)) : (c >> 1) }
            table[i] = c
        }
        var c: UInt32 = 0xFFFFFFFF
        for b in d { c = table[Int((c ^ UInt32(b)) & 0xFF)] ^ (c >> 8) }
        return c ^ 0xFFFFFFFF
    }

    public static func fromQr(_ text: String) -> AirQrPacket? {
        guard let raw = Data(base64Encoded: text.trimmingCharacters(in: .whitespacesAndNewlines)) else { return nil }
        guard raw.count >= 30, raw[0] == 0x41, raw[1] == 0x51 else { return nil }
        func u32(_ o: Int) -> UInt32 { raw[o..<o+4].withUnsafeBytes { $0.load(as: UInt32.self) }.littleEndian }
        func u16(_ o: Int) -> UInt16 { raw[o..<o+2].withUnsafeBytes { $0.load(as: UInt16.self) }.littleEndian }
        let tid = raw[3..<11].map { String(format: "%02x", $0) }.joined()
        let fid = u32(11); let total = u32(15); let idx = u32(19)
        let plen = Int(u16(23)); let crc = u32(25); let flags = raw[29]
        guard raw.count >= 30 + plen else { return nil }
        let payload = raw[30..<30+plen]
        guard crc32(payload) == crc else { return nil }
        return AirQrPacket(transferIdHex: tid, fileId: fid, totalChunks: total, chunkIndex: idx, payload: payload, flags: flags)
    }
}

public struct ManifestFile {
    public let name: String; public let size: UInt64
    public let chunks: Int; public let order: Int
}

public struct Manifest { public let chunkSize: Int; public let files: [ManifestFile] }

public func parseManifest(_ b: Data) -> Manifest? {
    var off = 8
    func rd(_ n: Int) -> Data { let d = b[off..<off+n]; off += n; return d }
    guard b.count > 12 else { return nil }
    let nlen: UInt16 = rd(2).withUnsafeBytes { $0.load(as: UInt16.self) }.littleEndian
    _ = rd(Int(nlen)); _ = rd(16)
    let paritySkip = 1; off += paritySkip
    let chunkSize: UInt32 = rd(4).withUnsafeBytes { $0.load(as: UInt32.self) }.littleEndian
    let fileCount: UInt32 = rd(4).withUnsafeBytes { $0.load(as: UInt32.self) }.littleEndian
    var files: [ManifestFile] = []
    for _ in 0..<fileCount {
        let nl: UInt16 = rd(2).withUnsafeBytes { $0.load(as: UInt16.self) }.littleEndian
        let name = String(data: rd(Int(nl)), encoding: .utf8) ?? "file"
        let size: UInt64 = rd(8).withUnsafeBytes { $0.load(as: UInt64.self) }.littleEndian
        _ = rd(8); _ = rd(32)
        let ml: UInt16 = rd(2).withUnsafeBytes { $0.load(as: UInt16.self) }.littleEndian
        _ = rd(Int(ml))
        let chunks: UInt32 = rd(4).withUnsafeBytes { $0.load(as: UInt32.self) }.littleEndian
        off += 3; off += 8
        let order: UInt32 = rd(4).withUnsafeBytes { $0.load(as: UInt32.self) }.littleEndian
        files.append(ManifestFile(name: name, size: size, chunks: Int(chunks), order: Int(order)))
    }
    return Manifest(chunkSize: Int(chunkSize), files: files)
}

public class TransferSession: ObservableObject {
    @Published public var status = "Idle"
    @Published public var progress = "0/0"
    private var transferId: String?
    private var mChunks: [Int: Data] = [:]
    private var mTotal = 0
    private var manifest: Manifest?
    private var chunks: [Int: [Int: Data]] = [:]
    private var done = false

    public func feed(_ text: String) {
        guard let pkt = AirQrPacket.fromQr(text) else { return }
        if transferId == nil { transferId = pkt.transferIdHex }
        guard pkt.transferIdHex == transferId else { return }
        if pkt.flags & UInt8(Flags.manifest) != 0 {
            mChunks[Int(pkt.chunkIndex)] = pkt.payload
            mTotal = Int(pkt.totalChunks)
            status = "Manifest \(mChunks.count)/\(mTotal)"
            if mChunks.count == mTotal && manifest == nil {
                var joined = Data()
                for i in 0..<mTotal { joined.append(mChunks[i] ?? Data()) }
                manifest = parseManifest(joined)
                status = "Manifest: \(manifest?.files.count ?? 0) files"
            }
            return
        }
        if pkt.flags & UInt8(Flags.done) != 0 { done = true; status = "Done"; return }
        var m = chunks[Int(pkt.fileId)] ?? [:]
        m[Int(pkt.chunkIndex)] = pkt.payload
        chunks[Int(pkt.fileId)] = m
        updateProgress()
    }

    private func updateProgress() {
        guard let mf = manifest else { return }
        var have = 0, total = 0
        for f in mf.files { total += f.chunks; have += min(chunks[f.order]?.count ?? 0, f.chunks) }
        progress = "\(have)/\(total)"
    }
}
