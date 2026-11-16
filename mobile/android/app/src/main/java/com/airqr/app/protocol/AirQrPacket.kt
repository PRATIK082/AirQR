package com.airqr.app.protocol

import java.nio.ByteBuffer
import java.nio.ByteOrder
import java.util.zip.CRC32
import android.util.Base64

object Flags {
    const val COMPRESSED = 1
    const val ENCRYPTED = 2
    const val FINAL = 4
    const val MANIFEST = 8
    const val DONE = 16
    const val ACK = 32
    const val PARITY = 64
}

data class AirQrPacket(
    val transferIdHex: String,
    val fileId: Int,
    val totalChunks: Int,
    val chunkIndex: Int,
    val payload: ByteArray,
    val flags: Int
) {
    companion object {
        fun crc32(b: ByteArray): Int {
            val c = CRC32()
            c.update(b)
            return c.value.toInt()
        }
        fun fromQr(text: String): AirQrPacket? {
            return try {
                val raw = Base64.decode(text.trim(), Base64.DEFAULT)
                if (raw.size < 30) return null
                if (raw[0] != 0x41.toByte() || raw[1] != 0x51.toByte()) return null
                val bb = ByteBuffer.wrap(raw).order(ByteOrder.LITTLE_ENDIAN)
                bb.position(3 + 8)
                val fileId = bb.int
                val total = bb.int
                val idx = bb.int
                val plen = bb.short.toInt() and 0xFFFF
                val crc = bb.int
                val flags = bb.get().toInt() and 0xFF
                val tid = raw.slice(3 until 11).map { "%02x".format(it) }.joinToString("")
                val payload = raw.slice(30 until 30 + plen).toByteArray()
                if (payload.size != plen) return null
                if (crc32(payload) != crc) return null
                AirQrPacket(tid, fileId, total, idx, payload, flags)
            } catch (e: Exception) { null }
        }
    }
}
