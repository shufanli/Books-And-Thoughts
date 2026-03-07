#!/bin/bash
# 一次性安装：装好依赖 + 注册开机自启的后台监听服务
# 安装后只需把书拖入仓库根目录，其他全自动。

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
PYTHON="$(which python3)"
LABEL="com.books-and-thoughts.watch"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"

echo "=== 1. 安装 Python 依赖 ==="
pip3 install -q -r "$SCRIPT_DIR/requirements.txt"
echo "    完成"

echo ""
echo "=== 2. Calibre（MOBI/AZW3 转换需要） ==="
if command -v ebook-convert &>/dev/null; then
    echo "    已安装，跳过"
else
    read -p "    是否安装 Calibre？(MOBI/AZW3 格式需要，其他格式不需要) [y/N] " ans
    if [[ "$ans" =~ ^[Yy]$ ]]; then
        brew install --cask calibre
        echo "    安装完成，重新打开终端后生效"
    else
        echo "    跳过（仅 MOBI/AZW3 受影响）"
    fi
fi

echo ""
echo "=== 3. 注册开机自启服务 ==="
mkdir -p "$HOME/Library/LaunchAgents"

cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>$LABEL</string>
    <key>ProgramArguments</key>
    <array>
        <string>$PYTHON</string>
        <string>$SCRIPT_DIR/watch.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>$REPO_ROOT</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/books-watch.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/books-watch.log</string>
</dict>
</plist>
EOF

# 重新加载（已存在则先卸载）
launchctl unload "$PLIST" 2>/dev/null || true
launchctl load "$PLIST"
echo "    服务已启动，开机自动运行"

echo ""
echo "======================================"
echo "安装完成！"
echo ""
echo "使用方式："
echo "  把任意 PDF/EPUB/MOBI/AZW3 文件拖入 → $REPO_ROOT"
echo "  自动转换后会出现在 _inbox/ 文件夹"
echo "  然后告诉 Claude：「读 _inbox 里的书」"
echo ""
echo "查看实时日志：tail -f /tmp/books-watch.log"
echo "======================================"
