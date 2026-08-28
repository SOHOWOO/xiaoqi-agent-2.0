# 小七 Windows 打包

## 构建 EXE

```bat
packaging\build_windows.bat
```

或手动：

```bat
cd packaging
pyinstaller xiaoqi.spec --noconfirm
```

生成：`dist\xiaoqi\xiaoqi.exe`（onedir 目录）

## 运行

双击 `dist\xiaoqi\xiaoqi.exe` → 独立窗口 → 首次启动配置 → 进入小七的房间。

- 无 CMD 黑窗（`console=False`）
- 无浏览器地址栏（PyWebView 内嵌窗口）
- 自动合并 HTTP + 语音服务（单进程，随机端口）
- 关闭窗口自动清理后台服务

## 用户数据（升级不丢）

| 数据 | 位置 |
|------|------|
| 配置 | `%APPDATA%\xiaoqi\config.json` |
| API Key | `%APPDATA%\xiaoqi\secrets.json`（权限保护） |
| 记忆 SQLite | `%APPDATA%\xiaoqi\xiaoqi_memory.db` |
| 日志 | `%APPDATA%\xiaoqi\logs\` |
| 声音 profile | `%APPDATA%\xiaoqi\profiles\` |

重新安装 / 升级**不会**覆盖以上数据。

## API Key 安全

- 只存在 `%APPDATA%\xiaoqi\secrets.json`（用户目录 + ACL 权限）
- 前端 / JS / HTML / EXE / 日志 / API 返回中**不出现**
- 浏览器经后端 `/api/tts` 代理，绝不直接拿 Key

## 安装程序（Setup.exe）

当前用 PyInstaller 的 onedir 直接分发（`dist\xiaoqi\` 整个目录）。
如需一键安装 + 桌面/开始菜单快捷方式 + 卸载入口，可后续用 Inno Setup：

```bat
REM 1. 安装 Inno Setup 6
REM 2. 用 packaging\installer.iss 编译
iscc packaging\installer.iss
```

生成 `dist\小七 Setup.exe`。

## 已知限制

- `faster_whisper` 被 exclude（可选依赖），本地 STT 需用户自行 pip 安装；默认用浏览器语音识别
- 首次联网需要 DeepSeek API Key 才能对话；阿里云 Key 可选（语音）
- VRM 模型需放入 `web/assets/avatar/xiaoqi.vrm`（当前用 Three.js Avatar）
