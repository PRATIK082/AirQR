if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('sw.js').catch(() => {});
}
// NOTE: camera is started by receiver.js startCamera().
// Do NOT add a second getUserMedia listener here - it races with the
// BarcodeDetector/jsQR scan loops.
