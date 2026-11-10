// AirQR Web Receiver (Chrome/Android BarcodeDetector)
const video = document.getElementById('video');
const log = (m) => { const p = document.getElementById('status'); if (p) p.textContent = m; console.log(m); };

let detector = null;
let scanning = false;
let transferId = null;
let manifest = null;
let files = {}; // fid -> {info, chunks:{}, dataCount, parityCount}
let done = false;

const crcTable = (() => {
  const t = new Uint32Array(256);
  for (let i = 0; i < 256; i++) {
    let c = i;
    for (let k = 0; k < 8; k++) c = (c & 1) ? (0xEDB88320 ^ (c >>> 1)) : (c >>> 1);
    t[i] = c >>> 0;
  }
  return t;
})();
function crc32(bytes) {
  let c = 0xFFFFFFFF;
  for (let i = 0; i < bytes.length; i++) c = crcTable[(c ^ bytes[i]) & 0xFF] ^ (c >>> 8);
  return (c ^ 0xFFFFFFFF) >>> 0;
}

function b64ToBytes(b64) {
  const bin = atob(b64);
  const out = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
  return out;
}

function readU16(dv, off) { return dv.getUint16(off, true); }
function readU32(dv, off) { return dv.getUint32(off, true); }
function readU64(dv, off) { return Number(dv.getBigUint64(off, true)); }

function parsePacket(text) {
  const raw = b64ToBytes(text.trim());
  if (raw.length < 30) return null;
  const dv = new DataView(raw.buffer);
  const magic = String.fromCharCode(raw[0], raw[1]);
  if (magic !== 'AQ') return null;
  const version = raw[2];
  const tidBytes = raw.slice(3, 11);
  const transferId = Array.from(tidBytes).map(b=>b.toString(16).padStart(2,'0')).join('');
  const fileId = readU32(dv, 11);
  const totalChunks = readU32(dv, 15);
  const chunkIndex = readU32(dv, 19);
  const payloadLen = readU16(dv, 23);
  const crc = readU32(dv, 25);
  const flags = raw[29];
  const payload = raw.slice(30, 30 + payloadLen);
  if (payload.length !== payloadLen) return null;
  if (crc32(payload) !== crc) return null;
  return { version, transferId, fileId, totalChunks, chunkIndex, payload, flags };
}

function parseManifest(bytes) {
  let off = 0;
  const dv = new DataView(bytes.buffer);
  const tid = bytes.slice(off, off+8); off += 8;
  const nlen = dv.getUint16(off, true); off += 2;
  const sender = new TextDecoder().decode(bytes.slice(off, off+nlen)); off += nlen;
  const salt = bytes.slice(off, off+16); off += 16;
  const parityCount = bytes[off]; off += 1;
  const chunkSize = dv.getUint32(off, true); off += 4;
  const fileCount = dv.getUint32(off, true); off += 4;
  const files = [];
  for (let i = 0; i < fileCount; i++) {
    const nl = dv.getUint16(off, true); off += 2;
    const name = new TextDecoder().decode(bytes.slice(off, off+nl)); off += nl;
    const size = readU64(dv, off); off += 8;
    const csize = readU64(dv, off); off += 8;
    const sha = Array.from(bytes.slice(off, off+32)).map(b=>b.toString(16).padStart(2,'0')).join(''); off += 32;
    const ml = dv.getUint16(off, true); off += 2;
    const mime = new TextDecoder().decode(bytes.slice(off, off+ml)); off += ml;
    const chunks = dv.getUint32(off, true); off += 4;
    const cm = bytes[off]; off += 1;
    const enc = bytes[off]; off += 1;
    const _r = bytes[off]; off += 1;
    const mtime = readU64(dv, off); off += 8;
    const order = dv.getUint32(off, true); off += 4;
    files.push({ name, size, compressedSize: csize, sha256: sha, mime, chunks, compression: cm, encrypted: !!enc, mtime, order });
  }
  return { transferId: tid, sender, salt, parityCount, chunkSize, files };
}

function assembleChunks(chunks, total) {
  let len = 0;
  for (let i = 0; i < total; i++) {
    if (!chunks[i]) return null;
    len += chunks[i].length;
  }
  const out = new Uint8Array(len);
  let off = 0;
  for (let i = 0; i < total; i++) {
    out.set(chunks[i], off);
    off += chunks[i].length;
  }
  return out;
}

async function startCamera() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } });
    video.srcObject = stream;
    await video.play();
    if ('BarcodeDetector' in window) {
      detector = new BarcodeDetector({ formats: ['qr_code'] });
      scanning = true;
      scanLoop();
      log('Scanning...');
    } else {
      log('BarcodeDetector not supported. Use Chrome on Android.');
    }
  } catch (e) {
    log('Camera error: ' + e.message);
  }
}

async function scanLoop() {
  while (scanning) {
    try {
      const codes = await detector.detect(video);
      for (const c of codes) {
        handleQR(c.rawValue);
      }
    } catch (e) {}
    await new Promise(r => setTimeout(r, 200));
  }
}

function handleQR(text) {
  const pkt = parsePacket(text);
  if (!pkt) return;
  if (transferId === null) transferId = pkt.transferId;
  if (pkt.transferId !== transferId) return;

  const FLAG_MANIFEST = 8, FLAG_DONE = 16, FLAG_ACK = 32;
  if (pkt.flags & FLAG_MANIFEST) {
    if (!manifest) {
      // collect
      if (!window._mChunks) window._mChunks = {};
      window._mChunks[pkt.chunkIndex] = pkt.payload;
      const total = pkt.totalChunks;
      const have = Object.keys(window._mChunks).length;
      log('Manifest ' + have + '/' + total);
      if (have === total && !manifest) {
        const bytes = assembleChunks(Object.values(window._mChunks).reduce((a,b,i)=>{a[i]=b;return a;},{}), total);
        // need index map
      }
    }
    return;
  }
  // For simplicity, manifest collection by index:
}

// Manifest collection state
window._mChunks = {};
window._mTotal = 0;

// Redo handleQR manifest properly
function handleQR2(text) {
  const pkt = parsePacket(text);
  if (!pkt) return;
  if (transferId === null) transferId = pkt.transferId;
  if (pkt.transferId !== transferId) return;

  const FLAG_MANIFEST = 8, FLAG_DONE = 16;
  if (pkt.flags & FLAG_MANIFEST) {
    window._mChunks[pkt.chunkIndex] = pkt.payload;
    window._mTotal = pkt.totalChunks;
    const have = Object.keys(window._mChunks).length;
    log('Manifest ' + have + '/' + window._mTotal);
    if (!manifest && have === window._mTotal) {
      const chunks = [];
      for (let i = 0; i < window._mTotal; i++) chunks[i] = window._mChunks[i];
      const bytes = assembleChunks(chunks, window._mTotal);
      manifest = parseManifest(bytes);
      log('Manifest received: ' + manifest.files.length + ' files');
      for (const f of manifest.files) {
        files[f.order] = { info: f, chunks: {}, dataCount: f.chunks };
      }
    }
    return;
  }
  if (pkt.flags & FLAG_DONE) {
    done = true;
    log('Done received');
    finalize();
    return;
  }
  const fid = pkt.fileId;
  if (!files[fid]) return;
  const fd = files[fid];
  // store chunk by index (only data chunks < dataCount)
  if (pkt.chunkIndex < fd.dataCount) {
    fd.chunks[pkt.chunkIndex] = pkt.payload;
    const have = Object.keys(fd.chunks).length;
    log('File ' + fid + ': ' + have + '/' + fd.dataCount);
  }
  if (Object.keys(files).every(f => Object.keys(files[f].chunks).length >= files[f].dataCount) && done) {
    finalize();
  }
}

function finalize() {
  if (!manifest) return;
  for (const fid of Object.keys(files)) {
    const fd = files[fid];
    const info = fd.info;
    const chunks = [];
    for (let i = 0; i < fd.dataCount; i++) chunks[i] = fd.chunks[i];
    const data = assembleChunks(chunks, fd.dataCount);
    if (!data) { log('File ' + fid + ' incomplete'); continue; }
    // compression not supported on web (zstd). If compression flag present, skip.
    const blob = new Blob([data], { type: info.mime });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = info.name.split('/').pop();
    a.click();
    log('Saved ' + info.name);
  }
}

// override handleQR
window.handleQR = handleQR2;

document.getElementById('start').addEventListener('click', startCamera);
// patch scanLoop to call handleQR
const _origScan = scanLoop;
scanLoop = async function() {
  while (scanning) {
    try {
      const codes = await detector.detect(video);
      for (const c of codes) window.handleQR(c.rawValue);
    } catch (e) {}
    await new Promise(r => setTimeout(r, 200));
  }
};
