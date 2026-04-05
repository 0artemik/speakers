"""Приводит requirements.txt к UTF-8 (pip в Linux не читает UTF-16)."""
from pathlib import Path
import sys


def main(path: str = "requirements.txt") -> None:
    p = Path(path)
    raw = p.read_bytes()
    if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
        text = raw.decode("utf-16")
    elif len(raw) > 6 and raw[1] == 0 and raw[3] == 0 and raw[0] < 0x80:
        text = raw.decode("utf-16-le")
    else:
        text = raw.decode("utf-8")
    p.write_text(text, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "requirements.txt")
