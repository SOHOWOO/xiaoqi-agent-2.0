"""小七 · 路径管理

区分三类路径：
- get_app_dir()      程序资源（PyInstaller bundle / 开发根目录）
- get_resource_dir() 前端资源（web/，打包后位于 _MEIPASS 内）
- get_user_data_dir() 用户数据（%APPDATA%/xiaoqi，升级不丢）
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

APP_NAME = "Xiaoqi"
APP_DIR_NAME = "xiaoqi"


def _frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def get_app_dir() -> Path:
    """程序所在目录（PyInstaller 冻结时为 _MEIPASS）。"""

    if _frozen():
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))

    return Path(__file__).resolve().parent


def get_resource_dir() -> Path:
    """前端 web/ 资源目录（打包后位于 bundle 内）。"""

    return get_app_dir() / "web"


def get_user_data_dir() -> Path:
    """用户数据目录：%APPDATA%/xiaoqi（Windows）。"""

    if os.name == "nt":
        base = Path(os.environ.get("APPDATA", Path.home()))
    else:
        base = Path(os.environ.get(
            "XDG_CONFIG_HOME",
            Path.home() / ".config",
        ))

    path = base / APP_DIR_NAME
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_memory_db_path() -> Path:
    """记忆 SQLite 路径：%APPDATA%/xiaoqi/xiaoqi_memory.db。"""

    return get_user_data_dir() / "xiaoqi_memory.db"


def get_secrets_path() -> Path:
    """API Key 存储路径（权限保护）。"""

    return get_user_data_dir() / "secrets.json"


def get_config_path() -> Path:
    """软件配置路径。"""

    return get_user_data_dir() / "config.json"


def get_logs_dir() -> Path:
    """日志目录。"""

    path = get_user_data_dir() / "logs"
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_voice_profile_dir() -> Path:
    """声音 profile 目录（用户数据，避免打包覆盖）。"""

    path = get_user_data_dir() / "profiles"
    path.mkdir(parents=True, exist_ok=True)
    return path
