# 改包记：几个绕不过去的坑

以前改 apk 都是 `apktool d` / `apktool b` 一条龙，这次这个包不行，一路踩过来记一下。

## apktool 得用 3.x

2.9.3 直接解不开：

```
brut.androlib.exceptions.DexUtil$UnsupportedFile: Dex version 040 is not supported
```

这个包 `targetSdk 37`，里面 10 个 dex 有 6 个是 `dex 040`。换 apktool 3.0.3 才认。
3.0.3 没有 `-all` 后缀的 jar，普通 jar 已经是 fat jar 了。

## 别用 apktool b 全量回编译

试过一次，能出包，但：

- 10 个 dex 全被降级成 `039`
- 所有条目从 deflate 变成 stored
- 体积从 514 MB 涨到 603 MB

装不装得上另说，光是"所有 dex 版本变了"这一条就足够让人不敢用。所以改成单 dex 替换：

1. smali 汇编器只重编改动的那一个 dex
2. [tools/repack.py](../tools/repack.py) 遍历基线 APK 的全部 16740 个条目，逐条搬过去，
   `compress_type` / `date_time` / `extra` / `external_attr` 全部沿用，只把目标 dex 换掉
3. `zipalign -p -f 4`（`-p` 是给 `.so` 做页对齐）
4. `apksigner sign`，v1 + v2 + v3

产物还是 514 MB 出头，和基线差不到 100 KB。

## 汇编目标版本要跟基线对上

smali 汇编器的 `-a` 参数不太好猜：`-a 34` 和 `-a 33` 都吐 `dex 040`，`-a 36` 直接报
`IllegalArgumentException: dexVersion must be within [0, 999]`。所以固定用 `-a 34`，
汇编完先跑 [tools/dexcheck.py](../tools/dexcheck.py) 看一眼 magic、adler32、sha1
三项，顺手确认补丁方法名确实进了 string 表：

```
$ python tools/dexcheck.py classes4.dex --contains safeParseZoom parseZoomValue
classes4.dex
  dex version : 040
  file size   : 12089256 (header says 12089256) OK
  adler32     : OK
  sha1        : OK
  safeParseZoom           : found
  parseZoomValue          : found
```

## 基线必须是上一轮的产物

这条差点翻车。第二轮如果拿原厂 `base_original.apk` 当基线，第一轮的补丁就白打了。
所以是 `final.apk` → `final2.apk` → `final3.apk` 一路滚下来，每轮打包前都 grep 一下
上一轮的方法还在不在。

好处是三轮用同一个 keystore，`adb install -r` 直接覆盖，不卸载、不丢数据、不用重新
给相机授权。

## 设备侧的几个小坑

Git Bash 会把 `/sdcard/...` 自动转成 `D:/.../sdcard/...`，adb 报路径不存在。全程
`export MSYS_NO_PATHCONV=1`，或者干脆用 `adb exec-out screencap -p > x.png`。

`dexdump.exe -o` 遇到中文路径报 `Invalid argument`，dex 得先拷到纯 ASCII 的临时目录。

`run-as <pkg> tar -xf /sdcard/x.tar` 会 `Permission denied`（scoped storage），改成先
推到 `/data/local/tmp` 再解。走 `tar -xf -` 从 stdin 灌也不行，报 `tar: EOF: Illegal seek`。

首次启动会弹一个「16 KB 对齐」警告，是原包自带 `.so` 的 ELF LOAD 段没对齐，跟改包无关，
点掉就行。

## 一个假阳性差点让我改回去

回归的时候出现过一次"点人像模式回到桌面"，一度以为是补丁把别的模式带崩了。

实际原因是底部那条模式栏切模式时会横向滑动，按钮坐标整体平移，脚本还按旧坐标点，
点到了别的按钮上。之后所有点击坐标都改成 `uiautomator dump` 现取，不再写死。

顺带一提，相机预览一直在重绘，`uiautomator dump` 经常报 `could not get idle state`，
得多试一次或者退回用 `screencap` 量坐标。
