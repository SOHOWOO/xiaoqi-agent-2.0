from core.simulator import LifeSimulator
from core.time_engine import make_aware
from core.presence import build_presence


def main():
    simulator = LifeSimulator(seed=42)

    now = make_aware(2026, 8, 20, 9, 0)
    later = make_aware(2026, 8, 20, 12, 30)

    result = simulator.simulate(now, later)

    print("=== 小七 Life Simulation ===")
    print(f"模拟时间：{now} -> {later}")
    print(f"当前 Slot：{result.life_state.current_slot_id}")
    print(f"当前活动：{result.life_state.current_activity}")
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

    current_slot = simulator.schedule_engine.get_slot(later)

    if isinstance(current_slot, str):
        print(f"\n当前状态：{current_slot}")
    else:
        presence = build_presence(current_slot, result.life_state)
        print("\n=== 小七当前状态 ===")
        print(presence.describe())


if __name__ == "__main__":
    main()
