# 两轮 smali 补丁（完整 unified diff）

## 01 · f.smali / parseZoomValue

```diff
--- f.smali.orig
+++ f.smali.patched
@@ -694,6 +694,123 @@
 
 
 # virtual methods
+
+.method public static parseZoomValue(Ljava/lang/String;)F
+    .registers 4
+
+    const/high16 v0, 0x3f800000    # 1.0f default
+
+    if-eqz p0, :cond_done
+
+    invoke-virtual {p0}, Ljava/lang/String;->length()I
+
+    move-result v1
+
+    if-eqz v1, :cond_nonempty
+
+    return v0
+
+    :cond_nonempty
+    const/4 v1, 0x0
+
+    invoke-virtual {p0, v1}, Ljava/lang/String;->charAt(I)C
+
+    move-result v1
+
+    const/16 v2, 0x30
+
+    if-lt v1, v2, :cond_dot
+
+    const/16 v2, 0x39
+
+    if-le v1, v2, :cond_numeric
+
+    :cond_dot
+    const/16 v2, 0x2e
+
+    if-eq v1, v2, :cond_numeric
+
+    const/16 v2, 0x2d
+
+    if-eq v1, v2, :cond_numeric
+
+    const/16 v2, 0x2b
+
+    if-eq v1, v2, :cond_numeric
+
+    const-string v2, "Wide"
+
+    invoke-virtual {v2, p0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z
+
+    move-result v2
+
+    if-eqz v2, :cond_sat
+
+    const v0, 0x3f266666    # 0.65f
+
+    return v0
+
+    :cond_sat
+    const-string v2, "SAT"
+
+    invoke-virtual {v2, p0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z
+
+    move-result v2
+
+    if-eqz v2, :cond_tele
+
+    const v0, 0x3f266666    # 0.65f
+
+    return v0
+
+    :cond_tele
+    const-string v2, "Tele3P5x"
+
+    invoke-virtual {v2, p0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z
+
+    move-result v2
+
+    if-eqz v2, :cond_tele2
+
+    const v0, 0x406ccccd    # 3.7f
+
+    return v0
+
+    :cond_tele2
+    const-string v2, "Tele"
+
+    invoke-virtual {v2, p0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z
+
+    move-result v2
+
+    if-eqz v2, :cond_master
+
+    const v0, 0x406ccccd    # 3.7f
+
+    return v0
+
+    :cond_master
+    return v0
+
+    :cond_numeric
+    :try_start_0
+    invoke-static {p0}, Ljava/lang/Float;->parseFloat(Ljava/lang/String;)F
+
+    move-result v0
+    :try_end_0
+    .catch Ljava/lang/NumberFormatException; {:try_start_0 .. :try_end_0} :catch_nfe
+
+    return v0
+
+    :catch_nfe
+    const/high16 v0, 0x3f800000
+
+    return v0
+
+    :cond_done
+    return v0
+.end method
+
 .method public A()V
     .locals 4
 
@@ -826,7 +943,7 @@
 
     .line 63
     .line 64
-    invoke-static {v2}, Ljava/lang/Float;->parseFloat(Ljava/lang/String;)F
+    invoke-static {v2}, Lcom/android/camera/ui/commonui/zoomui/widget/f;->parseZoomValue(Ljava/lang/String;)F
 
     .line 65
     .line 66
@@ -853,7 +970,7 @@
 
     .line 76
     .line 77
-    invoke-static {v3}, Ljava/lang/Float;->parseFloat(Ljava/lang/String;)F
+    invoke-static {v3}, Lcom/android/camera/ui/commonui/zoomui/widget/f;->parseZoomValue(Ljava/lang/String;)F
 
     .line 78
     .line 79
@@ -877,7 +994,7 @@
 
     .line 88
     .line 89
-    invoke-static {v1}, Ljava/lang/Float;->parseFloat(Ljava/lang/String;)F
+    invoke-static {v1}, Lcom/android/camera/ui/commonui/zoomui/widget/f;->parseZoomValue(Ljava/lang/String;)F
 
     .line 90
     .line 91
@@ -901,7 +1018,7 @@
 
     .line 100
     .line 101
-    invoke-static {v0}, Ljava/lang/Float;->parseFloat(Ljava/lang/String;)F
+    invoke-static {v0}, Lcom/android/camera/ui/commonui/zoomui/widget/f;->parseZoomValue(Ljava/lang/String;)F
 
     .line 102
     .line 103

```

## 02 · ZoomRuleState.smali / normalizeZoomMap

```diff
--- ZoomRuleState.smali.orig
+++ ZoomRuleState.smali.patched
@@ -16,6 +16,136 @@
     return-void
 .end method
 
+
+.method public static normalizeZoomValue(Ljava/lang/String;)Ljava/lang/String;
+    .locals 2
+
+    if-eqz p0, :cond_default
+
+    invoke-virtual {p0}, Ljava/lang/String;->length()I
+
+    move-result v0
+
+    if-eqz v0, :cond_default
+
+    const/4 v0, 0x0
+
+    invoke-virtual {p0, v0}, Ljava/lang/String;->charAt(I)C
+
+    move-result v0
+
+    const/16 v1, 0x30
+
+    if-lt v0, v1, :cond_dot
+
+    const/16 v1, 0x39
+
+    if-le v0, v1, :cond_numeric
+
+    :cond_dot
+    const/16 v1, 0x2e
+
+    if-eq v0, v1, :cond_numeric
+
+    const/16 v1, 0x2d
+
+    if-eq v0, v1, :cond_numeric
+
+    const/16 v1, 0x2b
+
+    if-eq v0, v1, :cond_numeric
+
+    const-string v1, "Wide"
+
+    invoke-virtual {v1, p0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z
+
+    move-result v1
+
+    if-eqz v1, :cond_sat
+
+    const-string p0, "0.65"
+
+    return-object p0
+
+    :cond_sat
+    const-string v1, "SAT"
+
+    invoke-virtual {v1, p0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z
+
+    move-result v1
+
+    if-eqz v1, :cond_tele
+
+    const-string p0, "0.65"
+
+    return-object p0
+
+    :cond_tele
+    const-string v1, "Tele3P5x"
+
+    invoke-virtual {v1, p0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z
+
+    move-result v1
+
+    if-eqz v1, :cond_tele2
+
+    const-string p0, "3.7"
+
+    return-object p0
+
+    :cond_tele2
+    const-string v1, "Tele"
+
+    invoke-virtual {v1, p0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z
+
+    move-result v1
+
+    if-eqz v1, :cond_master
+
+    const-string p0, "3.7"
+
+    return-object p0
+
+    :cond_master
+    const-string p0, "1.0"
+
+    return-object p0
+
+    :cond_numeric
+    return-object p0
+
+    :cond_default
+    const-string p0, "1.0"
+
+    return-object p0
+.end method
+
+.method public static normalizeZoomMap(Ljava/util/HashMap;)V
+    .locals 3
+
+    if-eqz p0, :cond_done
+
+    const-string v0, "pref_zoom_param"
+
+    invoke-virtual {p0, v0}, Ljava/util/HashMap;->get(Ljava/lang/Object;)Ljava/lang/Object;
+
+    move-result-object v1
+
+    if-eqz v1, :cond_done
+
+    invoke-virtual {v1}, Ljava/lang/Object;->toString()Ljava/lang/String;
+
+    move-result-object v1
+
+    invoke-static {v1}, Lcom/android/camera/setting/rule/states/ZoomRuleState;->normalizeZoomValue(Ljava/lang/String;)Ljava/lang/String;
+
+    move-result-object v2
+
+    invoke-virtual {p0, v0, v2}, Ljava/util/HashMap;->put(Ljava/lang/Object;Ljava/lang/Object;)Ljava/lang/Object;
+
+    :cond_done
+    return-void
+.end method
 
 # virtual methods
 .method public _configMutex(Lcom/android/camera/setting/rule/RuleTable$MutexConfig;Ljava/util/List;)Z
@@ -564,6 +694,7 @@
     .line 34
     .line 35
     move-result-object p1
+    invoke-static {p1}, Lcom/android/camera/setting/rule/states/ZoomRuleState;->normalizeZoomMap(Ljava/util/HashMap;)V
 
     .line 36
     if-eqz p1, :cond_1
@@ -869,6 +1000,7 @@
     .line 191
     .line 192
     move-result-object p1
+    invoke-static {p1}, Lcom/android/camera/setting/rule/states/ZoomRuleState;->normalizeZoomMap(Ljava/util/HashMap;)V
 
     .line 193
     if-eqz p1, :cond_a

```
