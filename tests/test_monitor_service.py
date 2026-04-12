from gtaol_dre_helper.models.config import RuntimeActionStep
from gtaol_dre_helper.models.config import RuntimeProfile
from gtaol_dre_helper.models.monitor import MonitorDependencies, MonitorState
from gtaol_dre_helper.services.monitor import MonitorService


def build_profile(name: str, toggle_key: str, toggle_vk_codes: tuple[int, ...]) -> RuntimeProfile:
    return RuntimeProfile(
        name=name,
        type="ceo",
        toggle_key=toggle_key,
        sequence=[],
        toggle_vk_codes=toggle_vk_codes,
    )


def test_monitor_state_activate_and_deactivate_manage_runtime_fields() -> None:
    # 验证开启与关闭监控时，会同步维护当前方案、菜单颜色和下次检查时间等运行时字段。
    profile = build_profile("方案 A", "f1", (112,))
    state = MonitorState(
        profiles={"f1": profile},
        regions={"ceo": (1, 2, 3, 4), "single": (5, 6, 7, 8)},
        next_check_at=1.5,
    )

    activated_profile = state.activate("f1")

    assert activated_profile is profile
    assert state.monitoring is True
    assert state.active_profile is profile
    assert state.active_profile_key == "f1"
    assert state.next_check_at == 0.0

    state.set_menu_color((1, 2, 3))
    state.deactivate()

    assert state.monitoring is False
    assert state.active_profile_key is None
    assert state.menu_color is None
    assert state.active_profile is None


def test_monitor_state_configure_resets_pressed_states_and_runtime_flags() -> None:
    # 验证重新加载配置时，会清空旧的按键状态并重置监控运行态。
    profile = build_profile("方案 A", "f1", (112,))
    state = MonitorState(
        monitoring=True,
        active_profile_key="f1",
        pressed_states={"legacy": True},
        menu_color=(1, 2, 3),
        next_check_at=2.0,
    )

    state.configure(
        profiles={"f1": profile},
        regions={"ceo": (1, 2, 3, 4), "single": (5, 6, 7, 8)},
    )

    assert state.profiles == {"f1": profile}
    assert state.pressed_states == {"f1": False}
    assert state.regions["ceo"] == (1, 2, 3, 4)
    assert state.monitoring is False
    assert state.active_profile is None
    assert state.menu_color is None
    assert state.next_check_at == 0.0


def test_handle_toggle_clears_active_profile_in_overview_when_turning_off() -> None:
    # 验证对同一方案重复触发开关键时，会关闭监控并向界面发送清空当前方案的概览消息。
    messages: list[object] = []
    service = MonitorService(
        post_message=lambda message: messages.append(message) is None,
        dependencies=MonitorDependencies(),
    )
    service.state.profiles = {
        "f1": build_profile("方案 A", "f1", (112,)),
    }

    service.handle_toggle("f1")
    service.handle_toggle("f1")

    last_message = messages[-1]

    assert service.state.monitoring is False
    assert service.state.active_profile_key is None
    assert isinstance(last_message, MonitorService.OverviewChanged)
    assert last_message.monitoring is False
    assert last_message.active_profile is None


def test_poll_triggered_profile_key_only_triggers_when_combo_is_fully_pressed() -> None:
    # 验证组合开关键只有在全部按键同时按下时才会触发一次，并在松开后重置状态。
    pressed_codes: set[int] = set()
    service = MonitorService(
        post_message=lambda _: True,
        dependencies=MonitorDependencies(
            is_vk_pressed=lambda vk_code: vk_code in pressed_codes,
        ),
    )
    service.state.profiles = {
        "ctrl+f1": build_profile("方案 A", "ctrl+f1", (17, 112)),
    }
    service.state.pressed_states = {"ctrl+f1": False}

    pressed_codes = {17}
    first_trigger = service.poll_triggered_profile_key()

    pressed_codes = {17, 112}
    second_trigger = service.poll_triggered_profile_key()

    pressed_codes = {17, 112}
    third_trigger = service.poll_triggered_profile_key()

    pressed_codes = {17}
    fourth_trigger = service.poll_triggered_profile_key()

    assert first_trigger is None
    assert second_trigger == "ctrl+f1"
    assert third_trigger is None
    assert fourth_trigger is None
    assert service.state.pressed_states["ctrl+f1"] is False


def test_run_ceo_monitor_cycle_executes_sequence_when_threshold_reached() -> None:
    # 验证 CEO 监控识别到满足人数阈值时，会执行当前方案动作序列并自动停止监控。
    messages: list[object] = []
    executed_sequences: list[list[RuntimeActionStep]] = []
    profile = RuntimeProfile(
        name="CEO 方案",
        type="ceo",
        toggle_key="f1",
        toggle_vk_codes=(112,),
        sequence=[
            RuntimeActionStep(
                keys=("ctrl", "c"),
                interval=0.05,
                hold=0.05,
                delay=0.1,
                times=1,
            )
        ],
    )
    service = MonitorService(
        post_message=lambda message: messages.append(message) is None,
        dependencies=MonitorDependencies(
            ocr_screen_region=lambda _: "2/4",
            parse_player_count=lambda _: 2,
            execute_sequence=lambda sequence: executed_sequences.append(list(sequence)),
        ),
    )
    service.state.profiles = {"f1": profile}
    service.state.regions = {"ceo": (1, 2, 3, 4), "single": (5, 6, 7, 8)}
    service.state.activate("f1")

    service.run_ceo_monitor_cycle()

    assert executed_sequences == [profile.sequence]
    assert service.state.monitoring is False
    assert service.state.active_profile is None
    assert any(
        isinstance(message, MonitorService.OverviewChanged) and message.monitoring is False
        for message in messages
    )


def test_run_single_monitor_cycle_caches_menu_color_before_detecting_change() -> None:
    # 验证卡单监控首次运行时只记录菜单基准颜色，不会提前执行动作序列。
    captured_regions: list[tuple[int, int, int, int]] = []
    executed_sequences: list[list[RuntimeActionStep]] = []
    profile = RuntimeProfile(
        name="卡单方案",
        type="single",
        toggle_key="f2",
        toggle_vk_codes=(113,),
        sequence=[
            RuntimeActionStep(
                keys=("f5",),
                interval=0.05,
                hold=0.05,
                delay=0.1,
                times=1,
            )
        ],
    )
    service = MonitorService(
        post_message=lambda _: True,
        dependencies=MonitorDependencies(
            get_screen_region_average_color=lambda region: captured_regions.append(region) or (10, 20, 30),
            execute_sequence=lambda sequence: executed_sequences.append(list(sequence)),
        ),
    )
    service.state.profiles = {"f2": profile}
    service.state.regions = {"ceo": (1, 2, 3, 4), "single": (5, 6, 7, 8)}
    service.state.activate("f2")

    service.run_single_monitor_cycle()

    assert captured_regions == [(5, 6, 7, 8)]
    assert service.state.menu_color == (10, 20, 30)
    assert executed_sequences == []
    assert service.state.monitoring is True


def test_run_single_monitor_cycle_executes_sequence_when_menu_color_changes() -> None:
    # 验证卡单监控在检测到菜单颜色变化后，会执行动作序列并自动停止监控。
    executed_sequences: list[list[RuntimeActionStep]] = []
    checked_regions: list[tuple[tuple[int, int, int, int], tuple[int, int, int]]] = []
    profile = RuntimeProfile(
        name="卡单方案",
        type="single",
        toggle_key="f2",
        toggle_vk_codes=(113,),
        sequence=[
            RuntimeActionStep(
                keys=("f5",),
                interval=0.05,
                hold=0.05,
                delay=0.1,
                times=1,
            )
        ],
    )
    service = MonitorService(
        post_message=lambda _: True,
        dependencies=MonitorDependencies(
            check_screen_region_color=lambda region, color: checked_regions.append((region, color)) or False,
            execute_sequence=lambda sequence: executed_sequences.append(list(sequence)),
        ),
    )
    service.state.profiles = {"f2": profile}
    service.state.regions = {"ceo": (1, 2, 3, 4), "single": (5, 6, 7, 8)}
    service.state.activate("f2")
    service.state.set_menu_color((10, 20, 30))

    service.run_single_monitor_cycle()

    assert checked_regions == [((5, 6, 7, 8), (10, 20, 30))]
    assert executed_sequences == [profile.sequence]
    assert service.state.monitoring is False
