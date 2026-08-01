#!/bin/bash
# ============================================================
# EWT360 刷时长工具 · APK 打包脚本
# John Studio (c) 2024-2026
# ============================================================
# 用法:
#   chmod +x build_apk.sh
#   ./build_apk.sh
#
# 前置条件 (Ubuntu/Debian):
#   sudo apt update
#   sudo apt install -y python3-pip python3-venv openjdk-17-jdk \
#       git unzip wget libssl-dev libffi-dev \
#       autoconf automake libtool pkg-config
#
#   pip3 install --upgrade buildozer cython
#
#   # 安装 Android SDK + NDK (按 buildozer 提示自动下载)
#
# ============================================================

set -e

echo "============================================"
echo "  EWT360 APK Builder · John Studio"
echo "============================================"

# 进入脚本所在目录
cd "$(dirname "$0")"

# 检查 buildozer
if ! command -v buildozer &> /dev/null; then
    echo "[ERROR] buildozer 未安装！"
    echo "  请运行: pip3 install --upgrade buildozer cython"
    exit 1
fi

echo "[INFO] 使用 buildozer 版本: $(buildozer --version 2>&1 | head -1)"
echo "[INFO] Python 版本: $(python3 --version)"
echo "[INFO] Java 版本:"
java -version 2>&1 | head -2

# 清理旧构建
echo ""
echo "[STEP] 清理旧构建缓存..."
rm -rf .buildozer
rm -rf bin

# 开始构建
echo ""
echo "[STEP] 开始构建 APK (debug)..."
echo "  这可能需要 10-30 分钟（首次需下载 SDK/NDK/依赖）"
echo ""

buildozer android debug 2>&1 | tee build.log

# 检查产物
echo ""
if [ -f "bin/EWT360刷时长工具-5.0-debug.apk" ] || ls bin/*.apk 1>/dev/null 2>&1; then
    echo "============================================"
    echo "  ✅ APK 构建成功！"
    echo "============================================"
    echo ""
    echo "  文件位置: $(ls -lh bin/*.apk | tail -1 | awk '{print $NF}')"
    echo ""
    echo "  安装方式:"
    echo "    1. adb install bin/*.apk"
    echo "    2. 或用手机文件管理器打开 APK 安装"
    echo ""
else
    echo "============================================"
    echo "  ❌ APK 构建失败！"
    echo "============================================"
    echo ""
    echo "  请查看 build.log 获取详细错误信息"
    echo ""
    echo "  常见解决方案:"
    echo "  1. 确认 JDK 17 已安装: java -version"
    echo "  2. 确认网络可访问 Google/Android 服务"
    echo "  3. 尝试: buildozer android clean 后重试"
    exit 1
fi
