# AirQR Protocol

Messages are JSON with minimal keys. Types:

| Type | Code | Sender | Receiver | Fields |
|------|------|--------|----------|--------|
| File Header | `fh` | Shows | Scans | `f` (path), `n` (chunks), `m` (MD5) |
| Chunk | `ch` | Shows | Scans | `f`, `i` (index), `d` (base64 data), `c` (CRC32) |
| File Footer | `ff` | Shows | Scans | `f`, `m` (MD5) |
| ACK | `ack` | Scans | Shows | `f`, `i`, `s` (ok/nak) |
| Manifest | `mf` | Shows | Scans | `paths` (list) |
| Done | `done` | Shows | Scans | (none) |

After all chunks, sender sends a manifest. Receiver verifies all files exist. Then sender sends "done" to signal completion.

## Resume

If the transfer is interrupted, use `--resume` on both sides to continue. Progress is saved to `transfer_state.json` in the working directory.

## Stale ACK Handling

When the sender finishes one chunk and moves to the next, the receiver's display may still show the PREVIOUS chunk's ACK QR. The sender's scanner finds it (type `ack` matches), but the index check fails. Instead of returning failure, the sender:

1. Pauses 0.1s
2. Re-scans for the next 0.6s window
3. Repeats until either the correct ACK arrives or the 3s deadline expires

The correct ACK arrives once the receiver processes the current data QR. This keeps the transfer flowing without unnecessary retries.

## ACK Persistence

The receiver calls `_ack(...)` which shows the ACK QR and immediately returns (0.1s sleep only for display refresh). The ACK QR stays visible until the next handler calls `_ack` again with a new index. This gives the sender unlimited time to scan the ACK.
