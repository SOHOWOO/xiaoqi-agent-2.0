from __future__ import annotations

from datetime import datetime

from ...life_loop import LifeLoop
from ...memory import (
    MemoryContextBuilder,
    MemoryRetriever,
    SQLiteMemoryStore,
)
from ...time_engine import DEFAULT_TZ
from .agent import XiaoqiAgent


def _build_chat(
    life_loop,
    response_provider=None,
):
    """基于给定 LifeLoop 组装 ChatService。"""

    from ...chat import ChatService

    retriever = MemoryRetriever(
        life_loop.memory_store,
        now_provider=lambda: life_loop.current_time,
    )

    context_builder = MemoryContextBuilder(retriever)

    return ChatService(
        life_loop=life_loop,
        memory_context_builder=context_builder,
        response_provider=response_provider,
    )


def _build_runtime(
    *,
    memory_db: str = "memories/xiaoqi_memory.db",
    seed: int = 42,
    response_provider=None,
):
    """组装一套 xiaoqi 核心运行时（LifeLoop + ChatService）。"""

    memory_store = SQLiteMemoryStore(memory_db)

    life_loop = LifeLoop(
        start_time=datetime.now(DEFAULT_TZ),
        seed=seed,
        memory_store=memory_store,
    )

    chat_service = _build_chat(
        life_loop,
        response_provider,
    )

    return life_loop, chat_service


def create_xiaoqi_agent(
    *,
    life_loop=None,
    chat_service=None,
    response_provider=None,
    memory_db: str = "memories/xiaoqi_memory.db",
    seed: int = 42,
    **kwargs,
) -> XiaoqiAgent:
    """创建 XiaoqiAgent（对应 OLV AgentFactory 的 xiaoqi_agent 分支）。

    可注入已有的 life_loop / chat_service；否则自动组装一套运行时。
    """

    if life_loop is None and chat_service is None:
        life_loop, chat_service = _build_runtime(
            memory_db=memory_db,
            seed=seed,
            response_provider=response_provider,
        )

    elif life_loop is not None and chat_service is None:
        chat_service = _build_chat(
            life_loop,
            response_provider,
        )

    elif life_loop is None:
        life_loop = chat_service.life_loop

    return XiaoqiAgent(
        life_loop=life_loop,
        chat_service=chat_service,
        **kwargs,
    )
