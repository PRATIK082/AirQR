package com.airqr.app.ui

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

@Composable
fun ReceiverScreen(log: String, progress: String, onStart: () -> Unit) {
    Column(Modifier.padding(16.dp)) {
        Text("AirQR Native Receiver (ML Kit)", style = MaterialTheme.typography.titleMedium)
        Spacer(Modifier.height(8.dp))
        Text("Point camera at sender screen. 30-50cm, avoid glare.", style = MaterialTheme.typography.bodySmall)
        Spacer(Modifier.height(8.dp))
        Button(onClick = onStart) { Text("Start Camera Scan") }
        Spacer(Modifier.height(8.dp))
        Text(progress)
        Text(log, style = MaterialTheme.typography.bodySmall)
    }
}
