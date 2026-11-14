# AirQR — Deep Competitive Research & Improvement Study

> Comparative analysis of QR-based offline file transfer tools and a feature/usability improvement plan for AirQR.

## 1. Scope & Method
This study analyzes publicly known QR-based offline transfer approaches (including tools commonly referenced as QRCast, QR Forge, and CLI tools such as qrcp-style utilities) and compares them against AirQR's implemented v1. Where a competitor's implementation is proprietary or undocumented, assumptions are stated explicitly and AirQR's design avoids copying any code, branding, or proprietary protocol.

## 2. Landscape Overview
QR-based file transfer tools generally fall into three categories:
1. **CLI utilities** (e.g., qrcp-style): generate a single QR encoding a URL or short payload; require a shared network for the actual transfer. *Not truly offline.*
2. **Screen-to-camera streamers**: split a file into chunks, encode each as QR, display sequentially; receiver scans and reassembles. Truly offline. This is AirQR's category.
3. **Hybrid (QR handshake + Wi-Fi Direct/Hotspot)**: use QR to exchange connection info, then transfer over a local network. Requires Wi-Fi capability.

AirQR targets category 2 (fully offline), which is the hardest and most differentiated.

## 3. Competitor Profiles (inferred)

### 3.1 QRCast-style tools
- **Protocol**: Typically JSON text payloads per QR frame; chunk index + base64 data; simple ACK via re-display.
- **Frame size/speed**: Conservative chunk sizes (~500–900 bytes) to fit low QR versions; frame interval ~1s.
- **Error recovery**: Per-chunk retry on timeout; no FEC; missing chunks require full re-send.
- **Compression**: Rarely; sometimes gzip for text.
- **Mobile UX**: Basic camera view, progress bar; limited pause/resume; manual save.
- **Missing features**: No encryption, no folder structure, no resume across restarts, no accessibility modes, no i18n.
- **Bottlenecks**: JSON overhead reduces throughput; re-sending whole file on failure.
- **Security weaknesses**: No integrity hash beyond CRC; no passphrase; auto-open risk.

### 3.2 QR Forge-style tools
- **Protocol**: Often proprietary binary-ish or JSON; may use higher QR versions with EC level L for density.
- **Frame size/speed**: Larger frames (up to ~2.5 KB) at EC-L; faster frame intervals (~0.4s) but fragile under motion blur.
- **Error recovery**: Selective retransmission of missing chunks via NAK; limited retry counts.
- **Compression**: Sometimes ZIP pre-compression only.
- **Mobile UX**: Polished scanner with overlay; progress ring; preview for images.
- **Missing features**: No FEC, no Argon2id encryption, no accessibility (large-text/high-contrast), no web PWA fallback.
- **Bottlenecks**: High density + low EC = high failure under glare/low light.
- **Security weaknesses**: Optional password often weak (PBKDF2 low iterations); no hash verification before open.

### 3.3 Generic CLI QR transfer (qrcp-style)
- **Protocol**: Encodes a URL; actual bytes move over HTTP on local network.
- **Offline**: No — requires shared Wi-Fi.
- **Advantage**: Very fast (network speed).
- **Disadvantage**: Not offline; requires pairing/network; not AirQR's goal.

## 4. Feature Comparison Matrix

| Feature | QRCast-style | QR Forge-style | Generic CLI | **AirQR v1** |
|---|---|---|---|---|
| Fully offline | Yes | Yes | No | Yes |
| Compact binary packets | No (JSON) | Partial | N/A | Yes |
| CRC32 per chunk | Yes | Yes | N/A | Yes |
| SHA-256 file verification | No | Partial | No | Yes |
| Compression (Zstd, skip media) | Rare | ZIP only | N/A | Yes |
| AES-256-GCM + Argon2id | No | Weak pwd | No | Yes |
| Reed-Solomon / RaptorQ FEC | No | No | No | Yes (module) |
| Selective retransmission | Partial | Yes | N/A | Yes |
| Resume across restarts | No | Partial | No | Yes |
| Folder structure preservation | No | Partial | Yes (network) | Yes |
| Bidirectional (PC↔phone) | Partial | Partial | Yes | Yes (PC side) |
| Mobile receiver (native) | Partial | Yes | No | Web PWA (native on roadmap) |
| Web PWA fallback | No | No | No | Yes |
| Accessibility modes | No | No | No | Planned (modes documented) |
| i18n (8 langs) | No | No | No | Partial (en + structure) |
| CLI (`airqr send/receive`) | No | No | Yes | Yes |
| Demo assets / docs | Minimal | Minimal | Good | Yes |

## 5. AirQR Advantages
1. **Compact binary protocol** reduces per-frame overhead vs JSON, increasing throughput.
2. **SHA-256 end-to-end verification** prevents silent corruption; competitors rely on CRC only.
3. **Strong crypto**: AES-256-GCM with Argon2id (memory-hard) vs weak passwords.
4. **FEC (Reed-Solomon)** recovers missing frames without restart — unique in this category.
5. **Compression awareness** (Zstd, skip already-compressed media) saves time/bandwidth.
6. **Folder structure + metadata** (MIME, mtime) preserved.
7. **Resume + selective retransmission** reduces repeated work on unstable links.
8. **Web PWA fallback** with offline support — rare among competitors.
9. **Packaging**: pip-installable cross-platform package with direct-run framework.
10. **Documentation & demo assets** (screenshots/GIF) improve onboarding.

## 6. AirQR Disadvantages / Gaps
1. **No native mobile apps yet** (Android/iOS) — competitors with native scanners feel faster; web PWA depends on BarcodeDetector (Chrome) and has lower throughput.
2. **FEC not enabled by default in main flow** (parity_count=0 in web mode; desktop defaults to 2 but padding/trim edge cases need hardening).
3. **No ACK on mobile web sender** — uses blind streaming loops, less efficient than ACK-driven.
4. **No adaptive QR params in practice** — choose_* functions exist but not fully wired to live scan success rate.
5. **No low-light/motion-blur guidance** beyond docs; no runtime lighting estimate.
6. **Accessibility modes** (large-text, high-contrast) documented but not implemented in UI.
7. **i18n** only English locale file present.
8. **No background transfer / notifications** on desktop.
9. **No external monitor/TV optimization** or watch-folder mode yet.
10. **No automated camera/low-light/motion-blur test harness** despite plan.

## 7. Usability Improvements (Prioritized)
### P0 (High impact, low effort)
- Add a **"Web-compatible mode" toggle** in UI (already CLI `--web`); auto-detect receiver capability.
- Show **live scan-quality indicator** (success rate) and suggest distance/lighting.
- **One-tap save** and **duplicate detection prompt** on mobile.
- **Progressive disclosure**: hide advanced QR controls by default; expose in settings.

### P1 (Medium)
- Implement **accessibility modes** (dark/light/large-text/high-contrast) with CSS variables and OS preference detection.
- Add **i18n** for all 8 languages; use locale files + fallback.
- **Watch-folder mode** for sender (auto-send new files).
- **External monitor/TV support**: fullscreen presenter with large QR and minimal chrome.
- **Preview** for received images/PDFs/text/audio/video in both desktop and web.

### P2 (Advanced)
- **Native mobile apps** (Kotlin Compose / Swift SwiftUI) with ML Kit / Vision decoders for speed.
- **Adaptive streaming** wired to real scan success rate and lighting estimate.
- **FEC enabled by default** with robust padding/trim and tests.
- **Background transfer** with notifications and resume.
- **Benchmarking harness** (camera sim, low-light, motion-blur, corrupted frames).

## 8. Security & Privacy Improvements
- Add **sender label verification** and **TOFU (trust on first use)** for repeated peers.
- **Rate-limit / lockout** on passphrase attempts (Argon2id already slow).
- **Clear security warnings** before opening executables/archives (already planned).
- **No telemetry**; document privacy policy (done).
- Consider **forward secrecy** not needed (one-shot passphrase).

## 9. Performance Targets (Benchmarks to Add)
- Throughput (KB/s) per EC level and QR version.
- Frame success rate under low light (lux levels) and motion blur (px/frame).
- End-to-end time for 100 MB ZIP (target: < 30 min on stable camera).
- Memory/CPU on mid-range Android.
- Retry rate and recovery time with FEC.

## 10. Recommended Roadmap (Next 3 Sprints)
- **Sprint 1**: Accessibility modes + i18n (en + hi) + scan-quality indicator + watch-folder.
- **Sprint 2**: Enable FEC by default + adaptive QR params + external monitor mode.
- **Sprint 3**: Native Android receiver (Kotlin + Compose + ML Kit) + preview + history.

## 11. Conclusion
AirQR already differentiates on protocol efficiency, integrity, crypto, and FEC — areas competitors neglect. The biggest gaps are **native mobile UX**, **accessibility/i18n**, and **adaptive runtime tuning**. Closing these will make AirQR clearly superior while keeping the fully-offline promise.