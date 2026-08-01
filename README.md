# EWT360 刷时长工具 · Android APK

**BETA5.0 · John Studio (c) 2024-2026 · 仅供技术学习研究**

## 项目说明

将 EWT360 刷时长工具从 Tkinter 桌面版移植到 Android 平台，使用 **Kivy** 框架重构 UI。

## 文件结构

```
EWT360_Android/
├── main.py              # 主程序（Kivy 版）
├── buildozer.spec       # Buildozer 打包配置
├── build_apk.sh         # 一键打包脚本
└── README.md            # 本文件
```

## 打包环境准备（Ubuntu/Debian）

### 1. 安装系统依赖

```bash
sudo apt update
sudo apt install -y \
    python3-pip python3-venv \
    openjdk-17-jdk \
    git unzip wget \
    libssl-dev libffi-dev \
    autoconf automake libtool pkg-config
```

### 2. 安装 Python 工具

```bash
pip3 install --upgrade buildozer cython
```

### 3. 验证环境

```bash
java -version          # 需 JDK 17
buildozer --version    # 需 buildozer 1.x
python3 --version      # 需 Python 3.8+
```

## 打包步骤

### 方式一：一键脚本

```bash
chmod +x build_apk.sh
./build_apk.sh
```

### 方式二：手动构建

```bash
# 初始化（首次运行会下载 Android SDK + NDK，约 2-5GB）
buildozer android debug

# 清理后重新构建
buildozer android clean
buildozer android debug

# 发布版本（需签名）
buildozer android release
```

## 输出

构建成功后，APK 文件位于：

```
bin/EWT360刷时长工具-5.0-debug.apk
```

## 安装到手机

### 方式一：ADB 安装

```bash
adb install bin/EWT360刷时长工具-5.0-debug.apk
```

### 方式二：手动安装

将 APK 传到手机，用文件管理器打开安装（需开启"允许未知来源"）。

## 与原版的主要差异

| 项目 | 桌面版 (Tkinter) | Android 版 (Kivy) |
|------|-------------------|-------------------|
| GUI 框架 | Tkinter | Kivy 2.3 |
| 窗口系统 | 桌面窗口 | 全屏/自适应 |
| 进度条 | ttk.Progressbar | Kivy ProgressBar |
| 日志框 | tk.Text | ScrollView + Label |
| 输入控件 | tk.Entry | Kivy TextInput |
| 依赖管理 | pip install | python-for-android |

## 核心逻辑完全一致

- ✅ 联网 Key 认证（GitHub Raw）
- ✅ 获取学校用户信息
- ✅ 获取课程详情 + 进度
- ✅ HMAC-SHA1 签名
- ✅ 心跳上报（120s 间隔）
- ✅ MD5 监测上报
- ✅ 多线程不阻塞 UI
- ✅ 可随时停止

## 注意事项

1. **首次构建**需要下载 Android SDK + NDK + 依赖，确保网络畅通且磁盘 ≥ 10GB
2. **JDK 版本**推荐 17（Android Gradle Plugin 兼容性最好）
3. **最低支持** Android 5.0 (API 21)
4. **目标版本** Android 14 (API 34)
5. 如需**发布版本**，需自行配置签名密钥

## 常见问题

### Q: 构建卡在 "Downloading Android SDK"
A: 检查网络，必要时配置代理或镜像源。

### Q: 报错 "JAVA_HOME not set"
A: `export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64`

### Q: APK 安装后闪退
A: 检查 Android 版本 ≥ 5.0，查看 logcat 日志：`adb logcat | grep python`

### Q: 请求超时/连接失败
A: 确保手机网络正常，工具需要访问 ewt360.com 相关接口。

## 免责声明

本工具仅供技术学习与研究使用，使用者应遵守相关法律法规及平台服务条款。

**ONLY JOHN STUDIO CANDO :)**