package com.airqr.app.transfer

import com.airqr.app.protocol.*

class TransferSession {
    var transferId: String? = null
    private val mChunks = mutableMapOf<Int, ByteArray>()
    private var mTotal = 0
    var manifest: Manifest? = null
        private set
    val chunks = mutableMapOf<Int, MutableMap<Int, ByteArray>>()
    var done = false

    fun feed(text: String): String {
        val pkt = AirQrPacket.fromQr(text) ?: return "ignored"
        if (transferId == null) transferId = pkt.transferIdHex
        if (pkt.transferIdHex != transferId) return "other-transfer"
        if (pkt.flags and Flags.MANIFEST != 0) {
            mChunks[pkt.chunkIndex] = pkt.payload
            mTotal = pkt.totalChunks
            if (mChunks.size == mTotal && manifest == null) {
                val total = (0 until mTotal).map { mChunks[it] ?: return "manifest-missing" }
                val joined = total.fold(byteArrayOf()) { a, x -> a + x }
                manifest = parseManifest(joined)
                manifest?.files?.forEach { chunks.getOrPut(it.order) { mutableMapOf() } }
                return "manifest ${mChunks.size}/$mTotal"
            }
            return "manifest ${mChunks.size}/$mTotal"
        }
        if (pkt.flags and Flags.DONE != 0) { done = true; return "done" }
        val m = chunks.getOrPut(pkt.fileId) { mutableMapOf() }
        m[pkt.chunkIndex] = pkt.payload
        return "file ${pkt.fileId} chunk ${pkt.chunkIndex}/${pkt.totalChunks}"
    }

    fun progress(): Pair<Int, Int> {
        val m = manifest ?: return 0 to 0
        var have = 0; var total = 0
        m.files.forEach { f -> total += f.chunks; have += (chunks[f.order]?.size ?: 0).coerceAtMost(f.chunks) }
        return have to total
    }

    /** Assembled bytes for one manifest file, or null if any chunk is missing. */
    fun assembledFile(order: Int): ByteArray? {
        val m = manifest ?: return null
        val f = m.files.firstOrNull { it.order == order } ?: return null
        val map = chunks[order] ?: return null
        if (map.size < f.chunks) return null
        var len = 0
        for (i in 0 until f.chunks) len += (map[i] ?: return null).size
        val out = ByteArray(len)
        var off = 0
        for (i in 0 until f.chunks) {
            val c = map[i] ?: return null
            c.copyInto(out, off)
            off += c.size
        }
        return out
    }
}
