# vivo V2454A 相机移植版人文街拍闪退修复记录

针对 `dev.x200.vivomod`（vivo X200 相机移植版 16.1.4.183）在 vivo V2454A / PD2454 / Android 17 上的人文街拍崩溃，做的两轮 smali 补丁与排障复盘。

## 结果

| 现象 | 状态 |
|---|---|
| 进入人文街拍立即闪退 | 已修复 |
| 点击 15 / 170 / 350mm 焦段闪退 | 已修复 |
| 6 个焦段逐个切换 | 全部正常 |
| 人文模式拍照 | 正常 |
| 普通模式变焦、人像/风光、前后摄、重启 | 无异常 |

## 根因

两轮崩溃同源：`CameraTypeZoomPoint.zoom` 字段在本机被填成**镜头标签字符串**（`"Wide"` / `"Tele3P5x"`），而代码多处直接 `Float.parseFloat` 解析它，抛 `NumberFormatException`。

- 第一轮：`ZoomCircleFrontManager.A()` —— 进入人文模块时
- 第二轮：`ZoomRuleState.changeState()` —— 点击焦段时，解析 `pref_zoom_param`

同一台机器上系统原生相机 13.0.55.13 的人文街拍完全正常，排除硬件 / HAL / 机型伪装因素。

## 修复

1. `f.smali` 新增 `parseZoomValue(String)F`，替换 `A()` 里 4 处裸 `parseFloat`。
2. `ZoomRuleState.smali` 新增 `normalizeZoomValue(String)String` 与 `normalizeZoomMap(HashMap)V`，在两处 `jSonStringToMap` 之后归一化 `pref_zoom_param`，让后续 `parseFloat` 与 `ListPreference.setValue` 都拿到数值字符串。

标签→倍率映射取自 `ZoomCompat.create()` 的真实配置：`Wide`/`SAT`→0.65、`Master`→1.0、`Tele3P5x`/`Tele`→3.7。

**没有裁焦段表**：裁表治不了崩溃（14mm 广角仍会拿到 `"Wide"`），且 `getZoomConvenientOptions()` 被 Food / AGENT / HighResolution / HUMANITIES 等 10+ 模块共用，改动会引入其它模式的变焦异常。

## 目录

- `docs/00-original-crash-report.txt` —— 第一轮原始诊断报告（已脱敏）
- `docs/01-root-cause.md` —— 两轮崩溃栈与证据链
- `docs/02-repack-workflow.md` —— 改包工具链、dex 040、单 dex 替换、重签名
- `docs/03-verification.md` —— 完整回归结果与已知问题
- `patches/` —— 两轮完整 smali diff 与应用说明

## 不包含的内容（安全）

仓库不含：任何 APK（单文件约 514 MB，超 GitHub 100 MB 限制且原厂包有版权）、签名证书与密码、应用私有数据、设备日志与截图、设备序列号。

## 已知问题（与本次修复无关）

录像模式下点录制会崩 `RuntimeException: Error! can not find any match zoom button. currentValue is 0.6`。A/B 回滚对照证实上一轮包同样会崩，属于移植包既有缺陷，本次未改。

仅用于个人设备调试记录，不分发任何 APK 或签名材料。


---

# 附录 A · 崩溃栈与证据链

# 崩溃栈与证据链

## 第一轮：进入人文街拍立即闪退

复现：打开应用（拍照模式正常）→ 点底部「人文街拍相机」箭头 → 100% 闪退回桌面。

```
FATAL EXCEPTION: main
Process: dev.x200.vivomod
java.lang.NumberFormatException: For input string: "Wide"
  at java.lang.Float.parseFloat(Float.java:556)
  at com.android.camera.ui.commonui.zoomui.widget.f.A(ZoomCircleFrontManager.java:63)
  at fg.m.W(ZoomUIController.java:122)
  at com.android.camera.ui.commonui.zoomui.base.e.execute(BaseZoomModelImpl.java:106)
  at com.android.camera.setting.SettingBusinessProcessor.changeCameraOrModule(...:962)
  at com.android.camera.humanities.ui.viewpagerui.HumanitiesViewPagerUI.onPageScrolled(...:24)
```

`CAP_VivoCameraCrashHandler: currentModule: humanities, isFront: false`。

## 第二轮：点击 15 / 170 / 350mm 焦段闪退

第一轮修好后能进人文、能拍照，但点两端焦段仍崩。设备 crash buffer 抓到 8 次：

```
FATAL EXCEPTION: main
java.lang.NumberFormatException: For input string: "Wide"       <- 15mm
java.lang.NumberFormatException: For input string: "Tele3P5x"  <- 170 / 350mm
  at java.lang.Float.parseFloat(Float.java:556)
  at com.android.camera.setting.rule.states.ZoomRuleState.changeState(ZoomRuleState.java:69)
  at com.android.camera.setting.rule.RuleStateBase.onSettingValueChange(...)
  at com.android.camera.setting.SettingBusinessProcessor.changeSetting(...:224)
  at com.android.camera.ui.commonui.zoomui.base.e.updateZoom(BaseZoomModelImpl.java:276)
  at com.android.camera.ui.commonui.zoomui.widget.circlegroup.ZoomCircleButton.onClick(...:11)
```

35 / 50 / 85mm 传的是数值字符串，因此不崩。

## 根因

`ZoomConfig$CameraTypeZoomPoint.zoom` 是 `String`，正常情况下应存倍率数值。移植包给 PD2454 写的反射兼容层 `dev/x200/vivomod/ZoomCompat` 在人文模块里把镜头标签（cameraType）串进了这个字段，导致所有直接 `parseFloat` 的调用点都会炸。上一轮只保护了 `f.smali` 的 4 处，规则引擎路径仍裸奔。

## 对照与排除项

- 同机同 HAL，系统原生相机 `com.android.camera` 13.0.55.13 的人文街拍正常，焦段 14 / 35 / 50 / 85 / 135mm
- 关闭系统动画：仍崩
- 进人文前预设 50mm 焦段：仍崩
- `run-as` 全量 grep 应用私有数据：无 `"Wide"`，非脏数据
- `/vendor/etc/camera/camera_config.xml` 里是小写 `wide`，与崩溃值大小写不一致，改 vendor 配置不对症且会影响系统相机
- 结论：问题在移植包自身代码，不在硬件 / HAL / 机型伪装 / 用户数据


---

# 附录 B · 改包流程与踩过的坑

# 改包流程与踩过的坑

## 工具链

| 项 | 说明 |
|---|---|
| JDK | 17 |
| apktool | **3.0.3**（2.9.3 不支持本包的 `dex 040`，会报 `Dex version 040 is not supported`） |
| smali 汇编 | apktool 内置 `com.android.tools.smali.smali.Main`，`-a 34` 输出 dex 040 |
| 签名 | build-tools 34.0.0 的 `zipalign` + `apksigner`，同证书覆盖安装 |
| 设备通道 | 系统 adb，`logcat -d -b main,system,crash` 抓栈 |

## 关键判断

1. **多 dex 与版本**：APK 有 10 个 dex，其中 classes.dex / 2 / 3 / 4 / 6 / 10 是 `dex 040`，classes5 / 7 / 8 / 9 是 `039`。重编哪个 dex 就要让输出 magic 与基线一致。
2. **不要用 `apktool b` 全量回编译**：实测会把所有 dex 降级到 039、所有条目变 stored，包从 514 MB 膨胀到 603 MB。
3. **单 dex 替换**：用 smali 汇编器只重编改动的 dex → Python `zipfile` 逐条复制基线 APK 的全部 16740 个条目（保留 `compress_type` / `date_time` / `extra` / `external_attr`），只替换该 dex → `zipalign -p -f 4` → `apksigner sign`（v1+v2+v3，最终验到 v3）。产物仍约 514 MB。
4. **基线铁律**：第二轮改包必须以第一轮产物 `final.apk` 为基线，不能用原厂 `base_original.apk`，否则丢掉上一轮补丁。改包前后都校验 `classes4.dex` 含 `parseZoomValue`。
5. **同签名覆盖安装**：`adb install -r` 即可，不卸载、不丢数据、不用重新授权。
6. **校验**：汇编后检查 dex 的 adler32 checksum 与 SHA-1 signature；用 baksmali 反汇编确认补丁存在、上一轮补丁未被波及。

## 环境坑

- Git Bash 的 MSYS 路径转换会把 `/sdcard/...` 变成 `D:/.../sdcard/...`，全程 `export MSYS_NO_PATHCONV=1` 或用 `adb exec-out`。
- 原生工具（如 `dexdump -o`）处理中文路径会乱码，用纯 ASCII 临时目录。
- `run-as <pkg> tar -xf /sdcard/x.tar` 会 Permission denied（scoped storage）；走 stdin 管道或 `/data/local/tmp`。
- 首次启动弹「16 KB 对齐」警告，是原包 so 自身 ELF LOAD 段未对齐，与改包无关。
- 底部模式栏会**滑动**，切模式后按钮坐标整体平移；回归必须用 `uiautomator dump` 现取坐标，否则旧坐标误触会产生假阳性。


---

# 附录 C · 回归验证结果

# 回归验证结果

判定标准：前台不回到 launcher，logcat 无 `FATAL EXCEPTION` / `NumberFormatException` / `am_crash` / `Fatal signal`。

| # | 操作 | 结果 |
|---|---|---|
| 1 | 冷启动 → 普通拍照模式 | 预览正常，无兼容警告残留 |
| 2 | 点底部箭头进入人文街拍 | 不闪退（上一轮成果防回归） |
| 3 | 逐个点击 15 / 35 / 50 / 85 / 170 / 350mm | **全部不闪退**，前台始终相机 |
| 4 | 人文模式拍照 | 生成新 JPG，文件非空 |
| 5 | 录像模式进入 | 正常 |
| 6 | 普通模式各变焦档 | 正常 |
| 7 | 人像 / 风光与夜景模式 | 正常 |
| 8 | 前后摄切换 | 正常 |
| 9 | 退出重进 | 稳定 |
| 10 | 对照原机系统相机人文焦段 | 行为一致（焦段条仍为移植包 6 档） |

最终 logcat 崩溃关键字计数：0。

## 已知既有缺陷（与补丁无关）

录像模式下点录制键会崩：

```
java.lang.RuntimeException: Error! can not find any match zoom button. currentValue is 0.6
  at com.android.camera.ui.commonui.zoomui.widget.circlegroup.a.K(ZoomCircleGroupManager.java:388)
  ... StatePreviewing_NormalVideo ...
```

**A/B 归因**：回滚到上一轮 `final.apk`，跑完全相同的「进录像 → 点录制」序列，同样崩溃且异常一致。因此属于移植包既有缺陷，不是本补丁引入，本次未修。

## 回滚

- 回到上一轮包：`adb install -r dist/final.apk`（同签名覆盖，数据不动）
- 回到原厂包：卸载 → 装 `base_original.apk` → 重新授权 → 恢复 `appdata.tar`（走 stdin 或 `/data/local/tmp`）


---

# 附录 D · 原始诊断报告

```text
vivo 相机移植版「人文街拍相机」闪退诊断报告
=====================================================
日期      2026-11-14
设备      vivo V2454A (PD2454), Android 17
          指纹 vivo/PD2454/PD2454:17/CP2A.260605.016_V000L1/261106232919:user/release-keys
故障应用  dev.x200.vivomod / com.android.camera.CameraActivity
          versionName 16.1.4.183, versionCode 160104183
          安装于 2026-11-14 14:19:53, base.apk 514.8 MB
对照应用  com.android.camera 13.0.55.13 (系统原生相机, 人文街拍正常)

【复现步骤】
1. 打开「vivo相机移植测试」(桌面第三行最右图标) → 拍照模式正常出图
2. 点击底部「人文街拍相机」箭头
   (id: dev.x200.vivomod:id/iv_layer_bottom_center_icon, bounds [0,2888][1440,3032])
3. 立即闪退回桌面，100% 必现

【崩溃堆栈】
FATAL EXCEPTION: main
Process: dev.x200.vivomod, PID: 8597
java.lang.NumberFormatException: For input string: "Wide"
  at jdk.internal.math.FloatingDecimal.readJavaFormatString(FloatingDecimal.java:2054)
  at java.lang.Float.parseFloat(Float.java:556)
  at com.android.camera.ui.commonui.zoomui.widget.f.A(ZoomCircleFrontManager.java:63)
  at com.android.camera.ui.commonui.zoomui.widget.f.o(ZoomCircleFrontManager.java:6)
  at fg.m.W(ZoomUIController.java:122)
  at eg.a$a.b(BaseZoomPresenter.java:35)
  at com.android.camera.ui.commonui.zoomui.base.e.execute(BaseZoomModelImpl.java:106)
  at com.android.camera.ui.ext.commonui.DefaultCommonUIHandler.updateAllUI(...:51)
  at com.android.camera.ui.ext.DefaultUICtlHandler.dispatchSettingEvent(...:350)
  at com.android.camera.setting.SettingBusinessProcessor.changeCameraOrModule(...:962)
  at com.android.camera.setting.SettingBusinessProcessor.onSettingsChange(...:24)
  at com.android.camera.setting.rule.SettingRuleManager.triggerStateChange(...:379)
  at com.android.camera.ui.core.CameraUIController.handleUICommand(...:389)
  at com.android.camera.viewpageui.viewpage2.d.onPageScrolled(AbsViewPageUI.java:68)
  at com.android.camera.humanities.ui.viewpagerui.HumanitiesViewPagerUI.onPageScrolled(...:24)
  ... Choreographer / ActivityThread.main

CAP_VivoCameraCrashHandler: currentModule: humanities, isFront: false
am_crash: [8597,0,dev.x200.vivomod,819477574,java.lang.NumberFormatException,For input string: "Wide",FloatingDecimal.java,2054,0]
崩溃前操作轨迹: C：<人文街拍相机>,[CameraPointButton],[app:id/iv_layer_bottom_center_icon]
                S：<>,[TextView],[app:id/module_camera_lens_ai_text]

【根因】
切换到 humanities 模块时，设置规则触发 changeCameraOrModule → updateAllUI，
变焦圆环 ZoomCircleFrontManager 把镜头标签字符串 "Wide" 当作数值焦距传给
Float.parseFloat，主线程抛 NumberFormatException，进程被杀，Activity force-crash。

【对照实验（关键）】
同一台机器、同一套相机 HAL、同一份 /vendor/etc/camera/camera_config.xml：
- 系统原生相机 13.0.55.13「人文街拍相机」→ 正常进入，黑白预览 + 14/35/50/85/135mm
  焦段 + ISO/快门/WB/EV 参数齐全
- 移植包 16.1.4.183 → 必崩
因此不是硬件、HAL、机型伪装或系统相机配置导致，问题在移植包自身代码/焦段配置。

【已实测排除】
- 关闭系统动画 (window/transition/animator_duration_scale = 0)：仍崩
- 进入人文前预设 50mm 焦段：仍崩
- run-as 全量 grep 应用私有数据 (shared_prefs/files/databases/cache)：无 "Wide"，非脏数据
- /vendor/etc/camera/camera_config.xml 中为小写 <ModuleType>wide</ModuleType>，
  与崩溃里的 "Wide" 大小写不一致，改 vendor 配置不对症且会影响系统相机（不推荐）

【修复建议】
1. 首选：换针对 PD2454/V2454A 的适配版，或回退一个移植版本。
   该包 2026-10-24/25 编译，其中 libvivomod_portrait.so 为 10-25 单独修改。
2. 改包：在 ZoomCircleFrontManager (混淆后 com.android.camera.ui.commonui.zoomui.widget.f.A)
   的 parseFloat 前加标签白名单 / try-catch，把 "Wide" 映射为 1.0f (主摄 1x)，重签名安装。
3. 临时绕过：设备已装 LSPosed，作用域仅勾 dev.x200.vivomod，
   hook java.lang.Float.parseFloat(String)：入参 "Wide" 时返回 1.0f。

【验证方法】
换包或打补丁后：打开应用 → 点底部人文街拍箭头 → 停留在相机界面且出现焦段条/黑白预览
即为修复；adb logcat -d -v threadtime | grep NumberFormatException 应无输出。

【本机环境备注】
TuTuAI 手机智控桥 (127.0.0.1:3000) 本次中途退出，操作经系统 adb 完成
(E:/11/tools/android-sdk/platform-tools/adb.exe, 设备 <DEVICE_SERIAL>)。
未修改任何系统文件，未清除应用数据，未删除照片；动画缩放已恢复 1.0。

```

---

# 附录 E · 补丁应用说明

# smali 补丁

两份 `unified diff`，对应两轮修复。应用前提是已用 apktool 3.0.3 反编译出 smali 目录。

| 文件 | 目标 | 所在 dex |
|---|---|---|
| `01-humanities-parseZoomValue.diff` | `com/android/camera/ui/commonui/zoomui/widget/f.smali` | `classes4.dex` (040) |
| `02-focal-normalizeZoomMap.diff` | `com/android/camera/setting/rule/states/ZoomRuleState.smali` | `classes3.dex` (040) |

## 应用方式

```bash
# 在反编译产物目录下
patch -p0 < 01-humanities-parseZoomValue.diff
patch -p0 < 02-focal-normalizeZoomMap.diff
```

diff 的文件名是 `f.smali.orig` / `f.smali.patched` 形式，实际使用时把路径改成对应 smali 文件的相对路径（例如 `smali_classes4/com/android/camera/ui/commonui/zoomui/widget/f.smali`）。

## 01：parseZoomValue

在 `f.smali`（`ZoomCircleFrontManager`）新增 `public static parseZoomValue(String)F`：

- 首字符为数字 / `.` / `-` / `+` → 走 `Float.parseFloat`（外层 try/catch 兜住格式异常）
- `"Wide"` / `"SAT"` → 0.65f
- `"Tele3P5x"` / `"Tele"` → 3.7f
- `"Master"` / 其它 / null → 1.0f

把 `A()V` 里 4 处 `invoke-static {vX}, Ljava/lang/Float;->parseFloat(...)` 换成调用该方法（寄存器依次 `v2` / `v3` / `v1` / `v0`）。

## 02：normalizeZoomMap

在 `ZoomRuleState.smali` 新增 `normalizeZoomValue(String)String` 与 `normalizeZoomMap(HashMap)V`；在 `changeState` 里两处 `GsonUtils.jSonStringToMap` 的 `move-result-object p1` 之后各插入一行调用。

归一化对象是 map 的 `pref_zoom_param`：把镜头标签换成数值字符串。这样该方法后面的两处 `Float.parseFloat` 以及 `ListPreference.setValue` 都拿到合法值——比只把崩溃点包起来更彻底。

## 重编译与签名

见 `docs/02-repack-workflow.md`。要点：分别用 `-a 34` 汇编两个 dex（输出 magic 040），逐条复制基线 APK 只替换这两个 dex，再 zipalign + apksigner。改动必须基于**已含第一轮补丁**的 APK。


---

# 附录 F · .gitignore

```
# 二进制与大文件产物
*.apk
*.apks
*.idsig
*.dex
*.so
*.jar
*.tar

# 签名材料与应用私有数据（绝不入库）
*.keystore
*.jks
keystore.pass
appdata.tar
package_dump.txt

# 设备日志与截图（可能含隐私）
log_*.txt
*.log
*.png
*.jpg
*.jpeg

# 本地工作目录
dist/
backup/
tools/

```
