#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查 dex 的基本健康度，以及某个方法名有没有真的写进去。

改包最容易翻车的地方是 dex 版本对不上（这个包的 classes4 是 dex 040，
smali 汇编器默认给 039），装上去表现是开机即崩或者类加载失败，
所以每次汇编完先跑一遍这个再打包。

用法：
    python dexcheck.py classes4.dex
    python dexcheck.py classes4.dex --contains safeParseZoom parseZoomValue
"""

import argparse
import hashlib
import struct
import sys
import zlib

DEX_MAGIC = b"dex\n"


def read_header(path):
    with open(path, "rb") as fh:
        head = fh.read(0x70)
    if len(head) < 0x70 or head[:4] != DEX_MAGIC:
        raise SystemExit("%s 不是合法 dex（magic 不对）" % path)

    checksum = struct.unpack("<I", head[8:12])[0]
    signature = head[12:32]
    file_size = struct.unpack("<I", head[32:36])[0]
    version = head[4:7].decode("ascii")

    with open(path, "rb") as fh:
        blob = fh.read()
    real_adler = zlib.adler32(blob[12:]) & 0xFFFFFFFF
    real_sha1 = hashlib.sha1(blob[32:]).digest()

    return {
        "version": version,
        "file_size": file_size,
        "real_size": len(blob),
        "checksum_ok": checksum == real_adler,
        "signature_ok": signature == real_sha1,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dex")
    ap.add_argument("--contains", nargs="*", default=[],
                    help="需要在 string 表里出现的方法名/类名")
    args = ap.parse_args()

    h = read_header(args.dex)
    ok = True
    print("%s" % args.dex)
    print("  dex version : %s" % h["version"])
    print("  file size   : %d (header says %d) %s"
          % (h["real_size"], h["file_size"],
             "OK" if h["real_size"] == h["file_size"] else "MISMATCH"))
    print("  adler32     : %s" % ("OK" if h["checksum_ok"] else "BAD"))
    print("  sha1        : %s" % ("OK" if h["signature_ok"] else "BAD"))
    ok = ok and h["real_size"] == h["file_size"] and h["checksum_ok"] and h["signature_ok"]

    if args.contains:
        with open(args.dex, "rb") as fh:
            blob = fh.read()
        for name in args.contains:
            hit = name.encode("utf-8") in blob
            print("  %-24s: %s" % (name, "found" if hit else "MISSING"))
            ok = ok and hit

    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
