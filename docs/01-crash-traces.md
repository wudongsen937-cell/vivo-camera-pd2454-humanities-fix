# 三条崩溃栈

三段栈都是从设备上 `logcat -b crash -v threadtime` 直接抓的，只删了 PID 和时间戳里的
无意义部分，其余原样。

## 一、点「人文街拍相机」立刻回桌面

百分百必现，拍照模式本身完全正常。栈长这样：

```
FATAL EXCEPTION: main
Process: dev.x200.vivomod, PID: 8597
java.lang.NumberFormatException: For input string: "Wide"
	at jdk.internal.math.FloatingDecimal.readJavaFormatString(FloatingDecimal.java:2054)
	at jdk.internal.math.FloatingDecimal.parseFloat(FloatingDecimal.java:122)
	at java.lang.Float.parseFloat(Float.java:556)
	at com.android.camera.ui.commonui.zoomui.widget.f.A(ZoomCircleFrontManager.java:63)
	at com.android.camera.ui.commonui.zoomui.widget.f.o(ZoomCircleFrontManager.java:6)
	at fg.m.W(ZoomUIController.java:122)
	at eg.a$a.b(BaseZoomPresenter.java:35)
	at eg.a$a.onSuccess(BaseZoomPresenter.java:2)
	at com.android.camera.ui.commonui.zoomui.base.e.execute(BaseZoomModelImpl.java:106)
	at eg.a.k(BaseZoomPresenter.java:60)
	at fg.m.Q2(ZoomUIController.java:410)
	at fg.m.h4(ZoomUIController.java:26)
	at com.android.camera.ui.ext.commonui.DefaultCommonUIHandler.updateAllUI(DefaultCommonUIHandler.java:51)
	at com.android.camera.ui.ext.DefaultUICtlHandler.dispatchSettingEvent(DefaultUICtlHandler.java:350)
	at com.android.camera.setting.SettingBusinessProcessor.changeCameraOrModule(SettingBusinessProcessor.java:962)
	at com.android.camera.ui.core.CameraUIController.handleEvent(CameraUIController.java:56)
	at com.android.camera.humanities.ui.viewpagerui.HumanitiesViewPagerUI.onPageScrolled(HumanitiesViewPagerUI.java:24)
```

倒着读一遍就很清楚了：滑到人文那一页 → 模块切换 → 整屏 UI 重刷 → 变焦圆环重算前端
倍率 → `ZoomCircleFrontManager.A()` 把某个 `String` 直接喂给 `parseFloat`。那个字符串
是 `"Wide"`。

`am_crash` 里也留了一条，说明系统侧确认是被杀而不是自杀：

```
I am_crash: [8597,0,dev.x200.vivomod,819477574,java.lang.NumberFormatException,
             For input string: "Wide",FloatingDecimal.java,2054,0]
```

## 二、修好之后，点 15 / 170 / 350mm 又崩

第一轮补完，进得去、能拍照，但点两端焦段还是崩。注意 35 / 50 / 85mm 是好的 ——
这条线索当时挺关键，说明只有最广和最远两档的 `zoom` 字段被写成了标签。

```
FATAL EXCEPTION: main
Process: dev.x200.vivomod, PID: 12113
java.lang.NumberFormatException: For input string: "Wide"
	at jdk.internal.math.FloatingDecimal.readJavaFormatString(FloatingDecimal.java:2054)
	at jdk.internal.math.FloatingDecimal.parseFloat(FloatingDecimal.java:122)
	at java.lang.Float.parseFloat(Float.java:556)
	at com.android.camera.setting.rule.states.ZoomRuleState.changeState(ZoomRuleState.java:69)
	at com.android.camera.setting.rule.SettingRuleManager.triggerStateChange(SettingRuleManager.java:180)
	at com.android.camera.setting.rule.RuleStateBase.onSettingValueChange(RuleStateBase.java:6)
	at com.android.camera.setting.preference.ListPreference.setValue(ListPreference.java:20)
	at com.android.camera.setting.preference.ListPreference.setValue(ListPreference.java:1)
	at com.android.camera.setting.SettingBusinessProcessor.changeSetting(SettingBusinessProcessor.java:224)
	at com.android.camera.setting.SettingManager.changeSetting(SettingManager.java:9)
	at com.android.camera.ui.commonui.zoomui.base.e.updateZoom(BaseZoomModelImpl.java:276)
	at com.android.camera.ui.commonui.zoomui.base.e.dataSubmit(BaseZoomModelImpl.java:15)
	at com.android.camera.ui.commonui.zoomui.model.CircleGroupModel.update(CircleGroupModel.java:66)
	at com.android.camera.ui.commonui.zoomui.base.e.execute(BaseZoomModelImpl.java:111)
	at eg.a.s(BaseZoomPresenter.java:93)
	at fg.m$a.c(ZoomUIController.java:290)
	at com.android.camera.ui.commonui.zoomui.widget.circlegroup.ZoomCircleButton.onClick(ZoomCircleButton.java:11)
```

点 170 / 350mm 走的是同一条路径，只是入参从 `"Wide"` 换成了 `"Tele3P5x"`。

`changeState` 里那行 `parseFloat` 读的是 `pref_zoom_param` 这个 setting 的当前值，
也就是说标签是从上层传进来的，不是它自己造的 —— 这解释了为什么光在第一轮的
`ZoomCircleFrontManager` 上打补丁不够。

## 三、拖焦段刻度滑杆还会崩

这条是第三轮才撞上的。点按钮走 `changeState`（第二轮已修），但拖焦段条下面那排刻度
滑杆走的是另一条路，`PreciseModel` 自己又解析了一次。

```
FATAL EXCEPTION: main
Process: dev.x200.vivomod, PID: 19024
java.lang.NumberFormatException: For input string: "Wide"
	at java.lang.Float.parseFloat(Float.java:556)
	at com.android.camera.ui.commonui.zoomui.model.PreciseModel.getZoomMessage(PreciseModel.java:379)
	at com.android.camera.ui.commonui.zoomui.model.PreciseModel.update(PreciseModel.java:3)
	at com.android.camera.ui.commonui.zoomui.model.PreciseModel.update(PreciseModel.java:1)
	at com.android.camera.ui.commonui.zoomui.base.e.execute(BaseZoomModelImpl.java:111)
	at eg.a.s(BaseZoomPresenter.java:93)
	at fg.m$a.c(ZoomUIController.java:290)
	at fg.m.v3(ZoomUIController.java:266)
	at n8.a.handleUICommand(HumanitiesUIHandler.java:135)
	at com.android.camera.ui.commonui.z.handleUICommand(CameraCommonUI.java:22)
	at com.android.camera.ui.core.CameraUIController.sendUICommand(CameraUIController.java:31)
	at com.android.camera.humanities.ui.widgetui.BCameraFunctionUI_V2.onProgressFocalChange(BCameraFunctionUI_V2.java:58)
	at com.android.camera.humanities.ui.widgetui.BCameraFunctionUI.onSettingChange(BCameraFunctionUI.java:8)
	at com.android.camera.humanities.addition.HumanitiesModeV2Addition.applyEntityDataToKeys(HumanitiesModeV2Addition.java:226)
	at com.android.camera.additionnew.AdditionManager.onSettingChanged(AdditionManager.java:48)
```

`onProgressFocalChange` 这个入口名说明得很直白：拖动进度（焦段）时触发。对应
smali 里就是 `PreciseModel.smali` 第 1457 行附近那一段：

```
.line 378
iget-object v0, v0, Lcom/android/camera/setting/api/ZoomConfig$CameraTypeZoomPoint;->zoom:Ljava/lang/String;

.line 380
invoke-static {v0}, Ljava/lang/Float;->parseFloat(Ljava/lang/String;)F

move-result v13
```

`zoom` 字段直接进 `parseFloat`，没有任何校验。

## 三处的关系

三处崩溃、三个类、两个 dex，但来源只有一个：`CameraTypeZoomPoint.zoom` 里存的东西
不是数字。所以修法也一样 —— 不是在崩溃点 try/catch 兜住了事，而是把标签先归一化成
数字，让后面所有依赖数值的地方（包括 `ListPreference.setValue` 和显示逻辑）都拿到
合法值。

## 排除掉的可能

怕自己先入为主，这些都是一条条实测排除的：

- 同机同 HAL，系统相机 13.0.55.13 进人文街拍正常（14/35/50/85/135mm 五档），排除硬件和 HAL
- 关掉 `window_animation_scale` / `transition_animation_scale` / `animator_duration_scale` 三个动画：照崩
- 进人文之前先手动选 50mm 再切：照崩
- `run-as` 把应用私有目录（shared_prefs / files / databases / cache）全 grep 了一遍，
  没有 `"Wide"`，不是脏数据
- `/vendor/etc/camera/camera_config.xml` 里写的是小写 `<ModuleType>wide</ModuleType>`，
  跟崩溃里的 `"Wide"` 大小写都对不上，改 vendor 配置不对症，还会影响系统相机
