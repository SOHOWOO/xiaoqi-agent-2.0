from datetime import timedelta

from core.life_loop import LifeLoop
from core.status import build_life_status, format_life_status
from core.time_engine import make_aware


def main():
    start = make_aware(2026, 8, 20, 9, 0)

    loop = LifeLoop(
        start_time=start,
        seed=42,
    )

    result = loop.tick(timedelta(hours=3, minutes=30))

    status = build_life_status(result.life_state)

    print("=== 小七 Life Loop ===")
    print(f"模拟时间：{start} -> {loop.current_time}")
    print(f"经过的 Slot：{result.slots_seen}")

    if result.events:
        print("\n发生的生活事件：")
        for event in result.events:
            print(
                f"- {event.event_type} "
                f"(slot={event.slot_id}, importance={event.importance})"
            )
    else:
        print("\n这段时间没有触发生活事件。")

    print("\n=== 小七当前状态 ===")
    print(format_life_status(status))


if __name__ == "__main__":
    main()
