[app]
title = EWT360刷时长工具
package.name = ewt360
package.domain = org.johnchen.ewt
source.dir = .
source.include_exts = py,png,jpg,kv,json,txt
version = 5.0

requirements =
    python3==3.9.16,
    kivy==2.3.0,
    requests==2.31.0

orientation = portrait
fullscreen = 0
android.permissions = INTERNET,ACCESS_NETWORK_STATE,WAKE_LOCK

[buildozer]
log_level = 2
warn_on_root = 1

[android]
android.api = 33
android.minapi = 21
android.ndk = 25b
android.ndk_path = /home/runner/.buildozer/android/platform/android-ndk-r25b
android.sdk_path = /home/runner/.buildozer/android/platform/android-sdk
android.accept_sdk_license = True
android.archs = arm64-v8a,armeabi-v7a
android.gradle_dependencies =
android.enable_androidx = True
android.build_tools_version = 34.0.0

[p4a]
p4a.branch = develop
p4a.source_dir =
p4a.local_recipes =
p4a.bootstrap = sdl2
