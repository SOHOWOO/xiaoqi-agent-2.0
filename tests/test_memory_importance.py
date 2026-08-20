from core.memory.importance import estimate_importance


def test_short_acknowledgement_is_low_importance():
    assert estimate_importance("好的") < 0.7


def test_laughter_is_low_importance():
    assert estimate_importance("哈哈哈哈") < 0.7


def test_preference_is_high_importance():
    assert estimate_importance("我喜欢吃草莓") >= 0.7


def test_future_plan_is_high_importance():
    assert estimate_importance("我明天要去上海出差") >= 0.7


def test_empty_message_has_zero_importance():
    assert estimate_importance("") == 0.0


def test_importance_is_bounded():
    messages = [
        "",
        "好的",
        "哈哈",
        "我喜欢吃草莓",
        "我明天要去上海出差",
        "我的生日是10月3日",
    ]

    for message in messages:
        importance = estimate_importance(message)

        assert 0.0 <= importance <= 1.0
