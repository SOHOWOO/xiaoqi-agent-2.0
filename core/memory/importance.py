from __future__ import annotations


_LOW_IMPORTANCE = {
    "嗯",
    "嗯嗯",
    "哦",
    "哦哦",
    "好的",
    "好",
    "行",
    "可以",
    "知道了",
    "收到",
    "哈哈",
    "哈哈哈",
    "哈哈哈哈",
}


_HIGH_IMPORTANCE_KEYWORDS = {
    "喜欢",
    "讨厌",
    "爱吃",
    "不吃",
    "生日",
    "住在",
    "工作",
    "上班",
    "学习",
    "计划",
    "打算",
    "今天",
    "明天",
    "下周",
    "以后",
    "最近",
}


def estimate_importance(text: str) -> float:
    """对用户消息进行轻量级重要性估计。

    这是一个确定性的基础版本。
    未来可以替换为 LLM-based importance classifier，
    而不需要修改 ChatService 或 MemoryManager。
    """

    text = text.strip()

    if not text:
        return 0.0

    if text.lower() in _LOW_IMPORTANCE:
        return 0.1

    if any(
        keyword in text
        for keyword in _HIGH_IMPORTANCE_KEYWORDS
    ):
        return 0.9

    # 普通完整消息给予中等偏低的重要性。
    return 0.5
