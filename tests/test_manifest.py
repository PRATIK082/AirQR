import sys, os, tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.manifest import collect_files, build_manifest, parse_manifest


def test_roundtrip():
    d = tempfile.mkdtemp()
    p = os.path.join(d, "a.txt")
    with open(p, "wb") as f:
        f.write(b"hello")
    files = collect_files(d)
    assert len(files) == 1
    files[0]["chunks"] = 2
    files[0]["compressed_size"] = 5
    sha = ["a" * 64]  # placeholder 64 hex
    # need valid hex sha256 length 64
    import hashlib
    sha = [hashlib.sha256(b"hello").hexdigest()]
    mb = build_manifest(os.urandom(8), files, sha, [0], False, b"\x00"*16, 2, 900, "sender")
    m = parse_manifest(mb)
    assert m["files"][0]["name"].endswith("a.txt")
    assert m["files"][0]["size"] == 5
    assert m["files"][0]["sha256"] == sha[0]
    assert m["parity_count"] == 2
