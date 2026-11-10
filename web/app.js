if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('sw.js').catch(() => {});
}
const btn = document.getElementById('start');
const video = document.getElementById('video');
btn.addEventListener('click', async () => {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } });
    video.srcObject = stream;
  } catch (e) {
    alert('Camera permission denied or unavailable: ' + e.message);
  }
});
