# AirQR Architecture Notes

## Sync Mechanism

The protocol avoids explicit handshake delays by using **continuous scanning** with **message-type filters**:

1. **Sender** shows a data QR and keeps it visible. Its scanner uses `_is_ack` filter to only accept ACK-type QR codes, ignoring its own data QR. If a stale ACK (from previous chunk) is received, the sender loops with a 0.1s pause until the receiver shows the new ACK.
2. **Receiver** shows an ACK QR after processing each data message, and **keeps it visible** until the next handler replaces it. Its scanner uses `_is_data` filter to only accept data-type QR codes, ignoring its own ACK QR.

This means:
- No dead zones — at least one screen always shows a QR code
- No fixed ACK display timeout — the sender has unlimited time to scan the ACK
- Transitions happen naturally when the next data QR is processed

## Scanner Filters

| Side | Filter | Accepts | Ignores |
|------|--------|---------|---------|
| Sender | `_is_ack` | `ack` (from receiver) | `fh`, `ch`, `ff`, `mf`, `done` |
| Receiver | `_is_data` | `fh`, `ch`, `ff`, `mf`, `done` (from sender) | `ack` |

## Key Constants

| Constant | File:Line | Default | Description |
|----------|-----------|---------|-------------|
| `CHUNK_SIZE` | `protocol.py:8` | 1200 | Raw bytes per chunk before base64 (~1600 chars in QR) |
| `ACK_TIMEOUT` | `protocol.py:9` | 2 | Seconds to wait for ACK before retry |
| `MAX_RETRIES` | `protocol.py:10` | 3 | Number of send attempts per message |

## For Faster Transfer

| Change | File | Effect |
|--------|------|--------|
| Increase `CHUNK_SIZE` | `protocol.py:8` | Fewer chunks per file (but larger QR codes) |
| Decrease `ACK_TIMEOUT` | `protocol.py:9` | Faster retry cycle (but less scan time) |
| Reduce `scanner.scan()` timeout in `_send_with_ack` | `sender.py:20` | Faster per-iteration scan (0.6s default) |
| Reduce `scanner.scan()` timeout in receiver loop | `receiver.py:48` | Faster data scan cycle (1.5s default) |
| Pre-generate QR images | `QRDisplay.show()` | Eliminate QR generation latency (~10-50ms per code) |
