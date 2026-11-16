package com.airqr.app.ui

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

@Composable
fun SenderScreen(params: SenderParams, stats: String, onPick: () -> Unit, onStart: () -> Unit, onStop: () -> Unit) {
    Column(Modifier.padding(16.dp)) {
        Text("AirQR Native Sender", style = MaterialTheme.typography.titleMedium)
        OutlinedTextField(value = params.chunkSize.toString(), onValueChange = { params.chunkSize = it.toIntOrNull()?.coerceIn(200, 2000) ?: 800 }, label = { Text("Chunk size (200-2000)") })
        OutlinedTextField(value = params.frameIntervalMs.toString(), onValueChange = { params.frameIntervalMs = it.toIntOrNull()?.coerceIn(500, 3000) ?: 1200 }, label = { Text("Frame interval ms") })
        OutlinedTextField(value = params.qrSize.toString(), onValueChange = { params.qrSize = it.toIntOrNull()?.coerceIn(180, 480) ?: 280 }, label = { Text("QR size px") })
        OutlinedTextField(value = params.parityCount.toString(), onValueChange = { params.parityCount = it.toIntOrNull()?.coerceIn(0, 4) ?: 0 }, label = { Text("Parity/FEC (0-4)") })
        Spacer(Modifier.height(8.dp))
        Text(stats, style = MaterialTheme.typography.bodySmall)
        Row {
            Button(onClick = onPick) { Text("Pick File") }
            Spacer(Modifier.width(8.dp))
            Button(onClick = onStart) { Text("Send") }
            Spacer(Modifier.width(8.dp))
            Button(onClick = onStop) { Text("Stop") }
        }
    }
}
