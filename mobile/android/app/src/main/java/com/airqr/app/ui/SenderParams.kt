package com.airqr.app.ui

data class SenderParams(
    var chunkSize: Int = 800,
    var frameIntervalMs: Int = 1200,
    var qrSize: Int = 280,
    var parityCount: Int = 0
) {
    fun chunkCount(fileSize: Long): Int = maxOf(1, ((fileSize + chunkSize - 1) / chunkSize).toInt())
    fun estLoopSeconds(totalFrames: Int): Int = totalFrames * frameIntervalMs / 1000
}
