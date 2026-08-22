from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class LLMConfig:
    """LLM 接入配置。"""

    api_key: str | None
    base_url: str
    model: str
    timeout: float


@dataclass(frozen=True)
class WebConfig:
    """Web 服务与虚拟时间流速配置。"""

    host: str
    port: int
    sim_minutes_per_real_second: float


@dataclass(frozen=True)
class PathsConfig:
    """运行时数据路径配置。"""

    db_path: Path
    canonical_dir: Path
    schedule_path: Path


@dataclass(frozen=True)
class AppConfig:
    """应用总配置。

    新模块（neurochemical / emotion / diary / proactive 2.0）统一从这里
    读取跨模块配置；各引擎内部的可调参数仍保留在各自模块中（与
    energy_engine 的 DEFAULT_PROFILES 风格一致）。
    """

    llm: LLMConfig
    web: WebConfig
    paths: PathsConfig
    sim_seed: int | None

    @classmethod
    def from_env(cls) -> "AppConfig":
        """从环境变量构建配置。

        保留与现有代码完全一致的环境变量名与默认值，便于逐步迁移。
        """

        api_key = (
            os.getenv("DEEPSEEK_API_KEY")
            or os.getenv("XIAOQI_LLM_API_KEY")
        )

        base_url = (
            os.getenv("XIAOQI_LLM_BASE_URL")
            or "https://api.deepseek.com"
        ).rstrip("/")

        model = os.getenv(
            "XIAOQI_LLM_MODEL",
            "deepseek-v4-flash",
        )

        try:
            timeout = float(
                os.getenv("XIAOQI_LLM_TIMEOUT", "60")
            )
        except ValueError as exc:
            raise ValueError(
                "XIAOQI_LLM_TIMEOUT must be a number"
            ) from exc

        if timeout <= 0:
            raise ValueError(
                "XIAOQI_LLM_TIMEOUT must be greater than zero"
            )

        host = os.getenv("XIAOQI_WEB_HOST", "0.0.0.0")
        port = int(os.getenv("XIAOQI_WEB_PORT", "8000"))

        try:
            sim_minutes_per_real_second = float(
                os.getenv("XIAOQI_SIM_MINUTES_PER_REAL_SECOND", "60")
            )
        except ValueError as exc:
            raise ValueError(
                "XIAOQI_SIM_MINUTES_PER_REAL_SECOND must be a number"
            ) from exc

        if sim_minutes_per_real_second <= 0:
            raise ValueError(
                "XIAOQI_SIM_MINUTES_PER_REAL_SECOND must be greater than zero"
            )

        db_path = Path(
            os.getenv("XIAOQI_DB_PATH", "memories/xiaoqi_memory.db")
        )
        canonical_dir = Path(
            os.getenv("XIAOQI_CANONICAL_DIR", "memories/canonical")
        )
        schedule_path = Path(
            os.getenv(
                "XIAOQI_SCHEDULE_PATH",
                "source-material/workday_schedule.json",
            )
        )

        raw_seed = os.getenv("XIAOQI_SIM_SEED")
        sim_seed = int(raw_seed) if raw_seed else None

        return cls(
            llm=LLMConfig(
                api_key=api_key,
                base_url=base_url,
                model=model,
                timeout=timeout,
            ),
            web=WebConfig(
                host=host,
                port=port,
                sim_minutes_per_real_second=sim_minutes_per_real_second,
            ),
            paths=PathsConfig(
                db_path=db_path,
                canonical_dir=canonical_dir,
                schedule_path=schedule_path,
            ),
            sim_seed=sim_seed,
        )
