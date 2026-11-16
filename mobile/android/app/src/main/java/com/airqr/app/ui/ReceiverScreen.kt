package com.airqr.app.ui

import android.Manifest as SysManifest
import android.content.ContentValues
import android.content.Context
import android.content.pm.PackageManager
import android.os.Build
import android.os.Environment
import android.provider.MediaStore
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.camera.core.CameraSelector
import androidx.camera.core.ExperimentalGetImage
import androidx.camera.core.ImageAnalysis
import androidx.camera.core.Preview
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.camera.view.PreviewView
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalLifecycleOwner
import androidx.compose.ui.unit.dp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.core.content.ContextCompat
import com.airqr.app.transfer.TransferSession
import com.google.mlkit.vision.barcode.BarcodeScannerOptions
import com.google.mlkit.vision.barcode.BarcodeScanning
import com.google.mlkit.vision.barcode.common.Barcode
import com.google.mlkit.vision.common.InputImage
import java.security.MessageDigest

private fun sha256Hex(b: ByteArray): String =
    MessageDigest.getInstance("SHA-256").digest(b).joinToString("") { "%02x".format(it) }

private fun saveToDownloads(context: Context, name: String, mime: String, bytes: ByteArray): String {
    val safe = name.substringAfterLast('/').takeIf { it.isNotBlank() } ?: "airqr-file"
    return try {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            val values = ContentValues().apply {
                put(MediaStore.Downloads.DISPLAY_NAME, safe)
                put(MediaStore.Downloads.MIME_TYPE, mime.ifBlank { "application/octet-stream" })
                put(MediaStore.Downloads.RELATIVE_PATH, Environment.DIRECTORY_DOWNLOADS + "/AirQR")
            }
            val resolver = context.contentResolver
            val uri = resolver.insert(MediaStore.Downloads.EXTERNAL_CONTENT_URI, values)
                ?: return "FAIL $safe (no MediaStore slot)"
            resolver.openOutputStream(uri)?.use { it.write(bytes) }
            "Saved Downloads/AirQR/$safe"
        } else {
            @Suppress("DEPRECATION")
            val dir = java.io.File(
                Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DOWNLOADS),
                "AirQR"
            )
            dir.mkdirs()
            val f = java.io.File(dir, safe)
            f.writeBytes(bytes)
            "Saved ${f.absolutePath}"
        }
    } catch (e: Exception) {
        "FAIL $safe (${e.message})"
    }
}

/** Real receiver: CameraX preview + ML Kit QR scan -> TransferSession -> Downloads. */
@OptIn(ExperimentalGetImage::class)
@Composable
fun ReceiverScreen() {
    val context = LocalContext.current
    val lifecycle = LocalLifecycleOwner.current
    var hasCam by remember {
        mutableStateOf(
            ContextCompat.checkSelfPermission(context, SysManifest.permission.CAMERA) ==
                PackageManager.PERMISSION_GRANTED
        )
    }
    val permLauncher = rememberLauncherForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { granted -> hasCam = granted }

    var scanning by remember { mutableStateOf(false) }
    var log by remember { mutableStateOf("Idle. Point the phone at the PC screen.") }
    var have by remember { mutableStateOf(0) }
    var total by remember { mutableStateOf(0) }
    var fileCount by remember { mutableStateOf(0) }
    var session by remember { mutableStateOf(TransferSession()) }
    var savedTid by remember { mutableStateOf<String?>(null) }
    var lastText by remember { mutableStateOf("") }
    var lastStatus by remember { mutableStateOf("") }

    val scanner = remember {
        BarcodeScanning.getClient(
            BarcodeScannerOptions.Builder()
                .setBarcodeFormats(Barcode.FORMAT_QR_CODE)
                .build()
        )
    }

    fun stopCamera() {
        scanning = false
        try {
            ProcessCameraProvider.getInstance(context).get().unbindAll()
        } catch (_: Exception) {
        }
    }

    fun maybeFinalize() {
        val m = session.manifest ?: return
        if (!session.done) return
        val tid = session.transferId ?: return
        if (savedTid == tid) return
        if (m.files.any { (session.chunks[it.order]?.size ?: 0) < it.chunks }) return
        val lines = m.files.map { f ->
            if (f.compressed) {
                "SKIP ${f.name}: sent compressed - resend from PC with --web (uncompressed)"
            } else if (f.encrypted) {
                "SKIP ${f.name}: encrypted transfers need the PC app"
            } else {
                val data = session.assembledFile(f.order)
                if (data == null) {
                    "FAIL ${f.name}: incomplete"
                } else if (sha256Hex(data) != f.sha256) {
                    "FAIL ${f.name}: corrupted, keep scanning"
                } else {
                    saveToDownloads(context, f.name, f.mime, data)
                }
            }
        }
        savedTid = tid
        log = lines.joinToString("\n")
    }

    fun startCamera(pv: PreviewView) {
        val future = ProcessCameraProvider.getInstance(context)
        future.addListener({
            try {
                val provider = future.get()
                val preview = Preview.Builder().build().also {
                    it.setSurfaceProvider(pv.surfaceProvider)
                }
                val analysis = ImageAnalysis.Builder()
                    .setBackpressureStrategy(ImageAnalysis.STRATEGY_KEEP_ONLY_LATEST)
                    .build()
                analysis.setAnalyzer(ContextCompat.getMainExecutor(context)) { proxy ->
                    val mediaImage = proxy.image
                    if (mediaImage == null) {
                        proxy.close()
                        return@setAnalyzer
                    }
                    val input = InputImage.fromMediaImage(
                        mediaImage, proxy.imageInfo.rotationDegrees
                    )
                    scanner.process(input)
                        .addOnSuccessListener { barcodes ->
                            for (b in barcodes) {
                                val text = b.rawValue ?: continue
                                if (text == lastText) continue
                                lastText = text
                                val status = session.feed(text)
                                val (h, t) = session.progress()
                                have = h
                                total = t
                                fileCount = session.manifest?.files?.size ?: 0
                                if (status != lastStatus) {
                                    lastStatus = status
                                    log = status
                                }
                                maybeFinalize()
                            }
                        }
                        .addOnCompleteListener { proxy.close() }
                }
                provider.unbindAll()
                provider.bindToLifecycle(
                    lifecycle, CameraSelector.DEFAULT_BACK_CAMERA, preview, analysis
                )
                scanning = true
                log = "Scanning... point at the PC screen"
            } catch (e: Exception) {
                log = "Camera error: ${e.message}"
            }
        }, ContextCompat.getMainExecutor(context))
    }

    DisposableEffect(Unit) {
        onDispose {
            try {
                ProcessCameraProvider.getInstance(context).get().unbindAll()
            } catch (_: Exception) {
            }
            try {
                scanner.close()
            } catch (_: Exception) {
            }
        }
    }

    var previewView by remember { mutableStateOf<PreviewView?>(null) }

    Column(Modifier.padding(16.dp)) {
        Text("AirQR Receiver", style = MaterialTheme.typography.titleMedium)
        Spacer(Modifier.height(4.dp))
        Text(
            "1. PC shows QRs  2. Start below  3. Point camera - files save themselves",
            style = MaterialTheme.typography.bodySmall
        )
        Spacer(Modifier.height(8.dp))
        if (!hasCam) {
            Button(onClick = { permLauncher.launch(SysManifest.permission.CAMERA) }) {
                Text("Allow Camera")
            }
        } else {
            AndroidView(
                factory { ctx ->
                    PreviewView(ctx).also { previewView = it }
                },
                modifier = Modifier.fillMaxWidth().height(320.dp)
            )
            Spacer(Modifier.height(8.dp))
            if (!scanning) {
                Button(onClick = {
                    val pv = previewView
                    if (pv != null) startCamera(pv) else log = "Preview not ready, try again"
                }) { Text("Start Scan") }
            } else {
                OutlinedButton(onClick = { stopCamera() }) { Text("Stop") }
            }
        }
        Spacer(Modifier.height(8.dp))
        if (total > 0) {
            Text("$have / $total chunks - $fileCount file(s)")
            LinearProgressIndicator(
                progress = { have.toFloat() / total.coerceAtLeast(1) },
                modifier = Modifier.fillMaxWidth()
            )
        }
        Spacer(Modifier.height(8.dp))
        Text(log, style = MaterialTheme.typography.bodySmall)
        Spacer(Modifier.height(8.dp))
        OutlinedButton(onClick = {
            stopCamera()
            session = TransferSession()
            savedTid = null
            lastText = ""
            lastStatus = ""
            have = 0
            total = 0
            fileCount = 0
            log = "Reset. Ready for next transfer."
        }) { Text("Reset") }
    }
}
