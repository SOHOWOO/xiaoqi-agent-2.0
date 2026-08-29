# -*- mode: python ; coding: utf-8 -*-
"""小七 · PyInstaller 构建配置

构建命令（在 packaging 目录执行）：
    pyinstaller xiaoqi.spec

输出：
    dist/xiaoqi/           # onedir 目录
    dist/xiaoqi/xiaoqi.exe # 入口
"""

import os
import sys
from pathlib import Path

# 项目根目录（spec 在 packaging/ 下，执行时 cwd 可能在 packaging/）
ROOT = Path(os.getcwd()).resolve()
if ROOT.name == "packaging":
    ROOT = ROOT.parent

a = Analysis(
    [str(ROOT / "xiaoqi_app.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[
        # 前端资源（web/）
        (str(ROOT / "web"), "web"),
        # 声音 profile（不含 reference.wav，已 gitignore）
        (str(ROOT / "voice" / "profiles"), "voice/profiles"),
        # 图标
        (str(ROOT / "assets"), "assets"),
        # 作息配置（LifeLoop 启动时读取）
        (str(ROOT / "source-material"), "source-material"),
    ],
    hiddenimports=[
        "http.server",
        "json",
        "threading",
        "asyncio",
        "urllib.request",
        "urllib.error",
        # PyWebView 运行时动态选择 Windows backend（edgechromium/mshtml）
        "webview",
        "webview.platforms.edgechromium",
        "webview.platforms.win32",
        "webview.platforms",
        # 记忆导入依赖（python-docx）
        "docx",
        "docx.document",
        "docx.opc.constants",
        "lxml",
        "lxml.etree",
        "lxml._elementpath",
        "et_xmlfile",
        # voice 模块
        "voice.engines",
        "voice.profile",
        "voice.status",
        "voice.providers.alibaba_tts",
        # appkit
        "appkit.paths",
        "appkit.config",
        "appkit.secrets",
        "appkit.providers",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "tkinter",
        "matplotlib",
        "scipy",
        "sympy",
        "pandas",
        "PIL",
        "tqdm",
        "onnxruntime",
        "faster_whisper",  # 可选，用户自行安装
        "torch",
        "ctranslate2",
        "huggingface_hub",
        "tokenizers",
        "av",
        "pytest",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# onedir 正确写法：
# EXE 只含 pyz + scripts，exclude_binaries=True（不内嵌二进制）
# 所有二进制/DLL/data 由 COLLECT 放入 _internal/，bootloader 从那里加载 python DLL
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="xiaoqi",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,               # 无 CMD 窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(ROOT / "assets" / "icon" / "xiaoqi.ico"),
    version=str(ROOT / "packaging" / "version_info.txt"),
)

# onedir：EXE + 外部资源目录（更稳定，资源独立，便于分发）
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="xiaoqi",
)

# 额外：复制快捷方式说明