# entry program: place the finished passport spread in /output.
# compose.py drew the spread (Republic of Aldermere, an invented country:
# data page with portrait and MRZ, visa page with stamps and a ferry-visa
# endorsement) and saved it as entry.png next to this file.
# This program only moves those bytes, so it needs no network and no
# clock, and every run writes the same file.
import os as _os
from pathlib import Path as _P

_PICTURE = _P(__file__).parent / "entry.png"
_TARGET = _P(_os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")) / "entry.png"
_LIMIT = 1048576
_PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
_JPEG_MAGIC = b"\xff\xd8\xff"


def _png_size(data):
    # width and height are big-endian uint32 at bytes 16..24 of a PNG.
    if data.startswith(_PNG_MAGIC) and data[12:16] == b"IHDR":
        w = int.from_bytes(data[16:20], "big")
        h = int.from_bytes(data[20:24], "big")
        return w, h
    return None


def run():
    data = _PICTURE.read_bytes()
    if not (data.startswith(_PNG_MAGIC) or data.startswith(_JPEG_MAGIC)):
        raise SystemExit("entry.png is neither a PNG nor a JPEG image")
    size = _png_size(data)
    if size is not None and (size[0] > 1024 or size[1] > 1024):
        raise SystemExit("entry.png is larger than 1024x1024 pixels")
    if len(data) > _LIMIT:
        raise SystemExit("entry.png is larger than the 1 MiB gate allows")
    _TARGET.parent.mkdir(parents=True, exist_ok=True)
    _TARGET.write_bytes(data)


run()
