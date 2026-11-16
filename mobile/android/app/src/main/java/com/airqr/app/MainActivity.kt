package com.airqr.app

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.material3.*
import androidx.compose.runtime.*
import com.airqr.app.ui.*

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            MaterialTheme {
                var tab by remember { mutableStateOf(0) }
                val params = remember { SenderParams() }
                var stats by remember { mutableStateOf("Select file to preview chunks.") }
                Column {
                    TabRow(selectedTabIndex = tab) {
                        Tab(selected = tab == 0, onClick = { tab = 0 }, text = { Text("Receive") })
                        Tab(selected = tab == 1, onClick = { tab = 1 }, text = { Text("Send") })
                    }
                    if (tab == 0) ReceiverScreen()
                    else SenderScreen(params, stats, onPick = { stats = "File picked" }, onStart = { stats = "Sending" }, onStop = {})
                }
            }
        }
    }
}
