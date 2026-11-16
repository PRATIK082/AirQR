package com.airqr.app.protocol

import java.nio.ByteBuffer
import java.nio.ByteOrder

data class ManifestFile(
    val name: String, val size: Long, val compressedSize: Long,
    val sha256: String, val mime: String, val chunks: Int,
    val compressed: Boolean, val encrypted: Boolean,
    val order: Int
)

data class Manifest(val chunkSize: Int, val parityCount: Int, val files: List<ManifestFile>)

fun parseManifest(b: ByteArray): Manifest? {
    return try {
        val bb = ByteBuffer.wrap(b).order(ByteOrder.LITTLE_ENDIAN)
        bb.position(8)
        val nlen = bb.short.toInt() and 0xFFFF
        val sbytes = ByteArray(nlen); bb.get(sbytes)
        bb.position(bb.position() + 16)
        val parity = bb.get().toInt() and 0xFF
        val chunkSize = bb.int
        val fileCount = bb.int
        val files = mutableListOf<ManifestFile>()
        repeat(fileCount) {
            val nl = bb.short.toInt() and 0xFFFF
            val nb = ByteArray(nl); bb.get(nb)
            val size = bb.long; val csize = bb.long
            val sha = ByteArray(32); bb.get(sha)
            val ml = bb.short.toInt() and 0xFFFF
            val mb = ByteArray(ml); bb.get(mb)
            val chunks = bb.int
            val cm = bb.get().toInt() and 0xFF
            val enc = bb.get().toInt() and 0xFF
            bb.get()
            val mtime = bb.long; val order = bb.int
            files.add(ManifestFile(String(nb), size, csize, sha.joinToString("") { "%02x".format(it) }, String(mb), chunks, cm != 0, enc != 0, order))
        }
        Manifest(chunkSize, parity, files)
    } catch (e: Exception) { null }
}
