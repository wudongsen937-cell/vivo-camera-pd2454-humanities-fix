# 回归验证

判定标准只有两条，够用了：

1. 操作完 `dumpsys window` 里 `mCurrentFocus` 还是 `dev.x200.vivomod/...CameraActivity`，
   也就是没掉回桌面
2. `logcat -d` 里 `FATAL EXCEPTION` / `NumberFormatException` / `am_crash` 三个关键字
   计数为 0

## 第三轮（最终包）

用 [tools/repack.py](../tools/repack.py) 以第二轮产物为基线重建，`classes4.dex`
换成含 `safeParseZoom` 的新版本，覆盖安装后跑：

| # | 操作 | 结果 |
|---|---|---|
| 1 | 冷启动 → 普通拍照模式 | 正常，无兼容警告残留 |
| 2 | 点底部箭头进人文街拍 | 进得去，焦段条六档、参数栏齐全 |
| 3 | 拖焦段刻度滑杆（左右各一次，900 ms） | 不崩，倍率跟着变（9mm ↔ 314mm） |
| 4 | 点 15 / 35 / 50 / 85 / 170 / 350mm | 六次全部不崩，前台始终是相机 |
| 5 | 点 350mm 后按快门 | 生成 `IMG_20261114_175040.jpg`，文件非空 |
| 6 | 普通模式各变焦档 | 正常 |
| 7 | 人像 / 风光与夜景模式 | 正常 |
| 8 | 前后摄切换 | 正常 |
| 9 | 杀进程重进 | 稳定 |

第 3 项是新补的那处，前两轮是崩的。

跑完这一串之后，三个崩溃关键字计数都是 0：

```
$ adb logcat -d | grep -c "FATAL EXCEPTION"
0
```

## 一个坐标上的教训

第一次跑第 4 项时六次都"没崩"，但截图一看倍率根本没变 —— 点在了焦距数字下面那排
ISO / SA / AF / WB / EV 参数上，把 ISO 从 AUTO 点成了 A。

人文模式的焦段按钮和设备坐标不在同一个高度：焦段条在 `y ≈ 2133`，参数行在
`y ≈ 2200`。差 70 px，肉眼在缩略图上看不出来，`adb shell input tap` 也不会给你任何
反馈。

所以后来每次都先截一张图核对亮的是哪一档，确认是真的点中了才记成通过。

## 已知的既有缺陷（和补丁无关）

录像模式下点录制键会崩：

```
java.lang.RuntimeException: Error! can not find any match zoom button. currentValue is 0.6
	at com.android.camera.ui.commonui.zoomui.widget.circlegroup.a.K(ZoomCircleGroupManager.java:388)
	at ba.w.x(StatePreviewing_VideoBase.java:74)
	at bb.t.x(StatePreviewing_NormalVideo.java:307)
	at com.android.camera.ui.commonui.bottommoduleui.BaseVideoBottomBar.onShutterButtonClicked(BaseVideoBottomBar.java:181)
```

**A/B 归因**：回滚装回第一轮的 `final.apk`，跑完全相同的"进录像 → 点录制"序列，
崩得一模一样，异常也是同一条。所以是移植包本来就有的问题，不是这三轮补丁带来的。
这次没修 —— 它的根因是 `ZoomCircleGroupManager` 找不到匹配 0.6 的变焦按钮，
和 `zoom` 字段的标签问题不是一回事。

## 回滚

```bash
# 回到上一轮（例如从第三轮退回第二轮）
adb install -r final2.apk

# 回到原厂包：得卸载重装，会丢数据和权限
adb uninstall dev.x200.vivomod
adb install base_original.apk
```

三个包都是同一个 keystore 签的，所以 `install -r` 是原地覆盖，数据不动。
退回原厂包则必须卸载，因为签名不同。
