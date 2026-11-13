// AirQR Web Sender (mobile/PC browser) - web-compatible (uncompressed, no encryption/FEC)
let sending = false;
let sendTask = null;

function u32(arr, v) { arr.push(v & 0xff, (v>>>8)&0xff, (v>>>16)&0xff, (v>>>24)&0xff); }
function u64(arr, v) {
  const n = BigInt(v);
  for (let i=0;i<8;i++) arr.push(Number((n >> BigInt(i*8)) & 0xffn));
}
function pushBytes(arr, bytes) { for (const b of bytes) arr.push(b); }

function chunkBytes(u8, size) {
  const out = [];
  for (let i=0;i<u8.length;i+=size) out.push(u8.slice(i, i+size));
  if (out.length===0) out.push(new Uint8Array(0));
  return out;
}

function encodePacket(pkt) {
  const buf = new ArrayBuffer(30 + pkt.payload.length);
  const dv = new DataView(buf);
  const u8 = new Uint8Array(buf);
  u8[0]=65; u8[1]=81;
  u8[2]=1;
  for (let i=0;i<8;i++) u8[3+i]=parseInt(pkt.transferId.substr(i*2,2),16);
  dv.setUint32(11, pkt.fileId, true);
  dv.setUint32(15, pkt.totalChunks, true);
  dv.setUint32(19, pkt.chunkIndex, true);
  dv.setUint16(23, pkt.payload.length, true);
  dv.setUint32(25, crc32(pkt.payload), true);
  u8[29]=pkt.flags;
  u8.set(pkt.payload, 30);
  let s = '';
  for (let i=0;i<u8.length;i++) s += String.fromCharCode(u8[i]);
  return btoa(s);
}

async function buildManifestBytes(transferId, files) {
  const parts = [];
  for (let i=0;i<8;i++) parts.push(parseInt(transferId.substr(i*2,2),16));
  const sender = "AirQR Web";
  const sb = new TextEncoder().encode(sender);
  parts.push(sb.length & 0xff, (sb.length>>8)&0xff);
  pushBytes(parts, sb);
  for (let i=0;i<16;i++) parts.push(0);
  parts.push(0); // parity
  u32(parts, 800); // chunk size
  u32(parts, files.length);
  for (let fi=0; fi<files.length; fi++) {
    const f = files[fi];
    const name = new TextEncoder().encode(f.name);
    parts.push(name.length & 0xff, (name.length>>8)&0xff);
    pushBytes(parts, name);
    u64(parts, f.size);
    u64(parts, f.compressedSize);
    for (let i=0;i<32;i++) parts.push(parseInt(f.sha256.substr(i*2,2),16));
    const mime = new TextEncoder().encode(f.mime);
    parts.push(mime.length & 0xff, (mime.length>>8)&0xff);
    pushBytes(parts, mime);
    u32(parts, f.chunks);
    parts.push(0,0,0); // compression, encrypted, reserved
    u64(parts, f.mtime);
    u32(parts, fi);
  }
  return new Uint8Array(parts);
}

async function startSend() {
  const input = document.getElementById('fileInput');
  if (!input.files.length) { document.getElementById('sendStatus').textContent = 'No file selected'; return; }
  sending = true;
  const fileObjs = [];
  for (const file of input.files) {
    const buf = await file.arrayBuffer();
    const u8 = new Uint8Array(buf);
    const chunks = chunkBytes(u8, 800);
    const shaBuf = await crypto.subtle.digest('SHA-256', u8);
    const shaHex = Array.from(new Uint8Array(shaBuf)).map(b=>b.toString(16).padStart(2,'0')).join('');
    fileObjs.push({ name: file.name, size: file.size, mime: file.type || 'application/octet-stream',
      chunks: chunks.length, compressedSize: u8.length, mtime: Math.floor(file.lastModified/1000),
      sha256: shaHex, data: chunks });
  }
  const tidBytes = crypto.getRandomValues(new Uint8Array(8));
  const transferId = Array.from(tidBytes).map(b=>b.toString(16).padStart(2,'0')).join('');
  const manifestBytes = await buildManifestBytes(transferId, fileObjs);
  const manifestChunks = chunkBytes(manifestBytes, 800);
  const packets = [];
  manifestChunks.forEach((mc, i) => {
    packets.push({ transferId, fileId: 0xFFFFFFFF, totalChunks: manifestChunks.length, chunkIndex: i, payload: mc, flags: 8 });
  });
  fileObjs.forEach((f, fi) => {
    const fid = fi+1;
    const dc = f.data.length;
    f.data.forEach((chunk, ci) => {
      let flags = 0;
      if (ci === dc-1) flags |= 4;
      packets.push({ transferId, fileId: fid, totalChunks: dc, chunkIndex: ci, payload: chunk, flags });
    });
  });
  packets.push({ transferId, fileId: 0, totalChunks: 0, chunkIndex: 0, payload: new Uint8Array(0), flags: 16 });

  const qrDiv = document.getElementById('qr');
  let idx = 0;
  const status = document.getElementById('sendStatus');
  while (sending) {
    const p = packets[idx % packets.length];
    const b64 = encodePacket(p);
    qrDiv.innerHTML = '';
    try { new QRCode(qrDiv, { text: b64, width: 280, height: 280 }); } catch(e) {}
    status.textContent = `Frame ${idx % packets.length + 1}/${packets.length} (looping)`;
    await new Promise(r => setTimeout(r, 1200));
    idx++;
  }
}

function stopSend() { sending = false; }

document.getElementById('startSend').addEventListener('click', () => { if (!sending) startSend(); });
document.getElementById('stopSend').addEventListener('click', stopSend);

// tab switching
document.getElementById('tabRecv').addEventListener('click', () => {
  document.getElementById('recvPanel').style.display = '';
  document.getElementById('sendPanel').style.display = 'none';
  document.getElementById('tabRecv').classList.add('active');
  document.getElementById('tabSend').classList.remove('active');
});
document.getElementById('tabSend').addEventListener('click', () => {
  document.getElementById('recvPanel').style.display = 'none';
  document.getElementById('sendPanel').style.display = '';
  document.getElementById('tabSend').classList.add('active');
  document.getElementById('tabRecv').classList.remove('active');
});
