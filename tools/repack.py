#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
按条目替换 APK 里的个别文件，其余条目原样搬过去。

为什么不用 apktool b 全量回编译：这个包有 10 个 dex、16740 个条目，
全量重建会把所有 dex 降级成 039、所有条目退化成 stored，包从 514 MB 涨到 603 MB，
而且签名后体积和加载行为都变了。只换需要换的那一两个 dex，其余原封不动，副作用最小。

用法：
    python repack.py --base final2.apk --out final3.apk \
        --replace classes4.dex=/tmp/classes4_new.dex \
        --replace classes3.dex=/tmp/classes3_new.dex

每个条目的 compress_type / date_time / external_attr / extra 都沿用基线，
所以 resources.arsc 仍然是 stored，lib/*.so 的可执行位也不会丢。
"""

import argparse
import copy
import os
import shutil
import sys
import zipfile


def parse_replace(items):
    mapping = {}
    for item in items or []:
        if "=" not in item:
            raise SystemExit("--replace 需要 entry=path 形式，收到: %r" % item)
        entry, path = item.split("=", 1)
        if not os.path.isfile(path):
            raise SystemExit("找不到替换文件: %s" % path)
        mapping[entry] = path
    return mapping


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True, help="基线 APK（必须是已含前序补丁的包）")
    ap.add_argument("--out", required=True, help="输出 APK")
    ap.add_argument("--replace", action="append", metavar="ENTRY=PATH")
    args = ap.parse_args()

    mapping = parse_replace(args.replace)
    if not mapping:
        raise SystemExit("至少给一个 --replace")

    tmp_out = args.out + ".part"
    with zipfile.ZipFile(args.base, "r") as src:
        names = set(src.namelist())
        for entry in mapping:
            if entry not in names:
                raise SystemExit("基线里没有这个条目: %s" % entry)

        with zipfile.ZipFile(tmp_out, "w", allowZip64=True) as dst:
            dst.comment = src.comment
            done = 0
            total = len(src.infolist())
            for info in src.infolist():
                if info.filename in mapping:
                    with open(mapping[info.filename], "rb") as fh:
                        data = fh.read()
                    # 复制一份 info，保留时间戳、权限位、压缩方式
                    dst.writestr(copy.copy(info), data)
                    print("  replace %-16s %10d -> %10d bytes"
                          % (info.filename, info.file_size, len(data)))
                else:
                    dst.writestr(copy.copy(info), src.read(info.filename))
                done += 1
                if done % 2000 == 0:
                    print("  ... %d/%d" % (done, total), file=sys.stderr)

    shutil.move(tmp_out, args.out)
    with zipfile.ZipFile(args.out, "r") as z:
        bad = z.testzip()
    base_size = os.path.getsize(args.base)
    out_size = os.path.getsize(args.out)
    print("done: %s  %d entries  %.1f MB -> %.1f MB"
          % (args.out, total, base_size / 1048576.0, out_size / 1048576.0))
    if bad:
        print("!! CRC 校验失败: %s" % bad)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
