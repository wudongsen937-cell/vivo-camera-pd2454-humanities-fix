# 三份 smali 补丁

三份 `unified diff`，对应三轮修复，按顺序应用。前提是已经用 apktool 3.0.3 反编译出
smali 目录。

| 文件 | 改动位置 | 所在 dex |
|---|---|---|
| `01-humanities-parseZoomValue.diff` | `ui/commonui/zoomui/widget/f.smali`（ZoomCircleFrontManager） | `classes4.dex` (040) |
| `02-focal-normalizeZoomMap.diff` | `setting/rule/states/ZoomRuleState.smali` | `classes3.dex` (040) |
| `03-precise-safeParseZoom.diff` | `ui/commonui/zoomui/model/PreciseModel.smali` | `classes4.dex` (040) |

diff 里的文件名写成的是 `f.smali.orig` / `f.smali.patched` 这种形式，因为它们是从
单文件对比里出来的。实际应用时把路径替换成对应 smali 文件的相对路径，比如：

```bash
cd smali_classes4
cp com/android/camera/ui/commonui/zoomui/widget/f.smali{,.orig}
patch -p0 f.smali.orig < ../../patches/01-humanities-parseZoomValue.diff
```

嫌麻烦就直接照着 diff 手工改，三处加起来不到 200 行 smali。

## 01：parseZoomValue

在 `f.smali` 里新增 `public static parseZoomValue(String)F`：

- 首字符是数字 / `.` / `-` / `+` → 照常 `Float.parseFloat`
- `"Wide"` / `"SAT"` → `0.65f`
- `"Tele3P5x"` / `"Tele"` → `3.7f`
- `"Master"` / null / 其它 → `1.0f`

然后把 `A()` 里四处 `invoke-static {vX}, Ljava/lang/Float;->parseFloat(...)` 换成调用
这个方法（寄存器依次是 `v2` / `v3` / `v1` / `v0`）。

## 02：normalizeZoomValue / normalizeZoomMap

在 `ZoomRuleState.smali` 新增两个方法，并在 `changeState` 里两处
`GsonUtils.jSonStringToMap(...)` 的 `move-result-object p1` 之后各插一行调用。

归一化的对象是 map 里的 `pref_zoom_param`，把标签换成数字串。这样做的原因是
`changeState` 后面除了 `Float.parseFloat`，还有 `ListPreference.setValue` 也会吃这个值 ——
只在崩溃那一行兜 try/catch 是不够的，得让往上传递的值本身就是干净的。

## 03：safeParseZoom

在 `PreciseModel.smali` 尾部新增 `public static safeParseZoom(String)F`，逻辑和
`parseZoomValue` 一样（先试 `parseFloat`，`NumberFormatException` 了再按标签映射，
未知值退 1.0f），但方法长在 `PreciseModel` 自己身上，不跨类依赖。

然后把 `getZoomMessage` 里那处 `parseFloat(v0)` 换成 `safeParseZoom(v0)`。

这处是拖焦段滑杆时走的路径，和第二处不是同一条链路，所以单独放一份，互不依赖。

## 重编译与签名

见 [docs/02-repack-notes.md](../docs/02-repack-notes.md)。要点重复一遍：

- 汇编用 `-a 34`，输出必须是 `dex 040`，跟基线一致
- 只替换改动的那一个 dex，其余条目原样搬（`tools/repack.py`）
- 改动必须基于**已经包含前面几轮补丁**的 APK，不能拿原厂包当基线
