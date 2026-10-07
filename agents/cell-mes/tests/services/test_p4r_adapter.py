"""Tests for P4R payload adapter timing behavior."""

from src.app.models.master import ProcessRouting, StdProcess
from src.app.services.digital_twin.failure_rules import load_p4r_failure_rules
from src.app.services.digital_twin.p4r_action_timing import build_action_timing_catalog
from src.app.services.digital_twin.p4r_adapter import P4RPayloadAdapter
from src.app.services.digital_twin.scenario_asset_parser import (
    load_scenario_yaml,
    p4r_process_mappings,
    scenario_assets,
    scenario_step_actions,
)


def _asset() -> dict:
    return {
        "idShort": "NX5500",
        "submodels": {
            "DtSimulationProfile": {
                "dt_resource_type": "CNC",
                "dt_type_id": "CNC",
            }
        },
    }


def _machine_asset_with_status(
    *,
    asset_id: str = "NX5500",
    resource_type: str = "CNC",
    gateway: str = "CncGateway",
    is_connected: bool | None = True,
    status: dict | None = None,
) -> dict:
    gateway_data = {"Status": status or {}}
    if is_connected is not None:
        gateway_data["IsConnected"] = is_connected
    return {
        "idShort": asset_id,
        "submodels": {
            "DtSimulationProfile": {
                "dt_resource_type": resource_type,
                "dt_type_id": resource_type,
            },
            gateway: gateway_data,
        },
    }


def _routing(*, routing_cycle_time: int | None, std_cycle_time: int = 120) -> ProcessRouting:
    return _routing_with_code(
        code="MILL",
        equipment_type="CNC",
        sequence=20,
        routing_cycle_time=routing_cycle_time,
        std_cycle_time=std_cycle_time,
    )


def _routing_with_code(
    *,
    code: str,
    equipment_type: str,
    sequence: int,
    routing_cycle_time: int | None,
    std_cycle_time: int = 120,
) -> ProcessRouting:
    std_process = StdProcess(
        id=sequence,
        code=code,
        name=code.title(),
        equipment_type=equipment_type,
        cycle_time_sec=std_cycle_time,
    )
    routing = ProcessRouting(
        id=sequence,
        product_id=2,
        std_process_id=std_process.id,
        sequence=sequence,
        cycle_time_sec=routing_cycle_time,
    )
    routing.std_process = std_process
    return routing


def _feeder_asset() -> dict:
    return {
        "idShort": "FEEDER",
        "submodels": {
            "DtSimulationProfile": {
                "dt_resource_type": "FEEDER",
                "dt_type_id": "FEEDER_TYPE",
                "capacity": 1,
            },
            "schedulerInfo": {
                "machineType": "FEEDER",
                "loaderSlots": 10,
                "unloaderSlots": 10,
            },
            "RobotGateway": {
                "Status": {
                    "loaderCount": 7,
                    "unloaderCount": 3,
                }
            },
        },
    }


def _qcm_asset() -> dict:
    return {
        "idShort": "EQUATOR_01",
        "submodels": {
            "DtSimulationProfile": {
                "dt_resource_type": "QCM",
                "dt_type_id": "QCM_EQUATOR",
                "capacity": 1,
                "mean_time_to_repair": 12000,
                "mean_time_between_failure": 99999999,
            },
            "RobotGateway": {"Status": {"status": "READY"}},
        },
    }


def _rack_asset(capacity: int = 6) -> dict:
    return {
        "idShort": "RACK_01",
        "submodels": {
            "DtSimulationProfile": {
                "dt_resource_type": "BUFFER",
                "dt_type_id": "BT_RACK_01",
                "capacity": capacity,
                "slot_mode": "SHARED",
            },
            "HttpGateway": {
                "Status": {
                    "allSlots": [
                        {"slotId": 1, "state": "occupied"},
                        {"slotId": 2, "state": "empty"},
                        {"slotId": 3, "state": "empty", "content": "product"},
                        {"slotId": 4, "state": "empty"},
                        {"slotId": 5, "state": "empty", "content": "raw"},
                        {"slotId": 6, "state": "empty"},
                    ]
                }
            },
        },
    }


def _cell2_assets_with_action_profiles() -> dict[str, dict]:
    return {
        "DH400": _asset_with_action_profile(
            asset_id="DH400",
            resource_type="CNC",
            actions={
                "ClampVise": {"defaultDurationSec": 10},
                "UnClampVise": {"defaultDurationSec": 10},
                "excute_main_program": {"defaultDurationSec": 5},
            },
        ),
        "DOOSAN_MOMA": _asset_with_action_profile(
            asset_id="DOOSAN_MOMA",
            resource_type="MM",
            actions={
                "move": {"defaultDurationSec": 60},
                "pick": {"defaultDurationSec": 120},
                "place": {"defaultDurationSec": 120},
                "detect_cnc": {"defaultDurationSec": 40},
                "open_cnc": {"defaultDurationSec": 120},
                "tray1_to_cnc": {"defaultDurationSec": 120},
                "cnc_to_tray2": {"defaultDurationSec": 120},
                "close_cnc": {"defaultDurationSec": 120},
                "start_process": {"defaultDurationSec": 60},
            },
        ),
        "EQUATOR_01": _asset_with_action_profile(
            asset_id="EQUATOR_01",
            resource_type="QCM",
            actions={
                "close_clamp": {"defaultDurationSec": 60},
                "measure": {"defaultDurationSec": 300},
                "open_clamp": {"defaultDurationSec": 60},
            },
        ),
        "RACK_01": _asset_with_action_profile(
            asset_id="RACK_01",
            resource_type="BUFFER",
            actions={
                "input": {"defaultDurationSec": 5},
                "output": {"defaultDurationSec": 5},
            },
        ),
    }


def _asset_with_action_profile(
    *,
    asset_id: str,
    resource_type: str,
    actions: dict[str, dict],
) -> dict:
    return {
        "idShort": asset_id,
        "submodels": {
            "DtSimulationProfile": {
                "dt_resource_type": resource_type,
                "dt_type_id": resource_type,
            },
            "P4RActionTimingProfile": {
                "Actions": {
                    action_id: {
                        "actionId": action_id,
                        "defaultDurationSec": values.get("defaultDurationSec"),
                        "timeOwnership": values.get("timeOwnership", "PROCESS_INTERNAL"),
                        "canContributeToRoutingCycleTime": values.get(
                            "canContributeToRoutingCycleTime", True
                        ),
                    }
                    for action_id, values in actions.items()
                }
            },
        },
    }


def test_build_process_info_uses_routing_cycle_time_before_std_process():
    adapter = P4RPayloadAdapter()
    process_info = adapter._build_process_info(
        "PLAT-A002",
        "MT_PLAT-A002",
        [_routing(routing_cycle_time=417)],
        {"NX5500": _asset()},
    )

    operation = process_info[0]["PROCESS_OPERATION_INFO"][0]
    assert operation["PROCESSING_TIME"] == "417"


def test_build_process_info_falls_back_to_std_process_cycle_time():
    adapter = P4RPayloadAdapter()
    process_info = adapter._build_process_info(
        "PLAT-A002",
        "MT_PLAT-A002",
        [_routing(routing_cycle_time=None, std_cycle_time=120)],
        {"NX5500": _asset()},
    )

    operation = process_info[0]["PROCESS_OPERATION_INFO"][0]
    assert operation["PROCESSING_TIME"] == "120"


def test_build_process_info_uses_action_profile_when_mapping_is_present():
    adapter = P4RPayloadAdapter()
    assets = {
        "FEEDER": _asset_with_action_profile(
            asset_id="FEEDER",
            resource_type="FEEDER",
            actions={"load": {"defaultDurationSec": 12}},
        )
    }
    breakdowns = []

    process_info = adapter._build_process_info(
        "PLAT-A002",
        "MT_PLAT-A002",
        [
            _routing_with_code(
                code="LOAD",
                equipment_type="FEEDER",
                sequence=10,
                routing_cycle_time=30,
            )
        ],
        assets,
        [],
        [{"process_code": "LOAD", "op_ids": ["OP-B01"], "time_mode": "ACTION_PROFILE"}],
        [
            {
                "step_id": "1",
                "op_id": "OP-B01",
                "asset": "FEEDER",
                "gateway": "RobotGateway",
                "action": "load",
                "raw_action": "{{acq.sub1}}/RobotGateway/Commands/load",
            }
        ],
        build_action_timing_catalog(assets),
        breakdowns,
    )

    operation = process_info[0]["PROCESS_OPERATION_INFO"][0]
    assert operation["PROCESSING_TIME"] == "12"
    assert breakdowns[0]["mode"] == "ACTION_PROFILE"
    assert breakdowns[0]["action_profile_sec"] == 12


def test_build_process_info_adds_action_profile_to_routing_cycle():
    adapter = P4RPayloadAdapter()
    assets = {
        "NX5500": _asset_with_action_profile(
            asset_id="NX5500",
            resource_type="CNC",
            actions={
                "open_door": {"defaultDurationSec": 5},
                "is_M20": {
                    "defaultDurationSec": 0,
                    "timeOwnership": "STATE_CHECK",
                    "canContributeToRoutingCycleTime": False,
                },
            },
        ),
        "UR_ROBOT": _asset_with_action_profile(
            asset_id="UR_ROBOT",
            resource_type="CR",
            actions={
                "detect": {"defaultDurationSec": 10},
                "cycle_start": {"defaultDurationSec": 20},
            },
        ),
    }
    breakdowns = []

    process_info = adapter._build_process_info(
        "PLAT-A002",
        "MT_PLAT-A002",
        [_routing(routing_cycle_time=120)],
        assets,
        [],
        [
            {
                "process_code": "MILL",
                "op_ids": ["OP-B02", "OP-B03"],
                "time_mode": "ROUTING_CYCLE_PLUS_ACTION_PROFILE",
            }
        ],
        [
            {
                "step_id": "11",
                "op_id": "OP-B02",
                "asset": "UR_ROBOT",
                "gateway": "RobotGateway",
                "action": "cycle_start",
                "raw_action": "{{acq.sub3}}/RobotGateway/Commands/cycle_start",
            },
            {
                "step_id": "12",
                "op_id": "OP-B02",
                "asset": "NX5500",
                "gateway": "CncGateway",
                "action": "is_M20",
                "raw_action": "{{acq.main}}/CncGateway/Queries/is_M20",
            },
            {
                "step_id": "13",
                "op_id": "OP-B02",
                "asset": "NX5500",
                "gateway": "CncGateway",
                "action": "open_door",
                "raw_action": "{{acq.main}}/CncGateway/Commands/open_door",
            },
            {
                "step_id": "16",
                "op_id": "OP-B02",
                "asset": "UR_ROBOT",
                "gateway": "RobotGateway",
                "action": "detect",
                "raw_action": "{{acq.sub3}}/RobotGateway/Commands/detect",
            },
            {
                "step_id": "23",
                "op_id": "OP-B03",
                "asset": "NX5500",
                "gateway": "CncGateway",
                "action": "is_M20",
                "raw_action": "{{acq.main}}/CncGateway/Queries/is_M20",
            },
        ],
        build_action_timing_catalog(assets),
        breakdowns,
    )

    operation = process_info[0]["PROCESS_OPERATION_INFO"][0]
    assert operation["PROCESSING_TIME"] == "155"
    assert breakdowns[0]["base_sec"] == 120
    assert breakdowns[0]["action_profile_sec"] == 35
    assert len(breakdowns[0]["components"]) == 3
    assert {item["reason"] for item in breakdowns[0]["skipped_actions"]} == {"CAN_NOT_CONTRIBUTE"}


def test_build_process_info_falls_back_when_action_mapping_has_no_profile_match():
    adapter = P4RPayloadAdapter()
    warnings = []
    breakdowns = []

    process_info = adapter._build_process_info(
        "PLAT-A002",
        "MT_PLAT-A002",
        [
            _routing_with_code(
                code="LOAD",
                equipment_type="FEEDER",
                sequence=10,
                routing_cycle_time=30,
            )
        ],
        {"FEEDER": _feeder_asset()},
        warnings,
        [{"process_code": "LOAD", "op_ids": ["OP-B01"], "time_mode": "ACTION_PROFILE"}],
        [
            {
                "step_id": "1",
                "op_id": "OP-B01",
                "asset": "FEEDER",
                "gateway": "RobotGateway",
                "action": "load",
                "raw_action": "{{acq.sub1}}/RobotGateway/Commands/load",
            }
        ],
        build_action_timing_catalog({"FEEDER": _feeder_asset()}),
        breakdowns,
    )

    operation = process_info[0]["PROCESS_OPERATION_INFO"][0]
    assert operation["PROCESSING_TIME"] == "30"
    assert warnings == ["LOAD action profile 매칭 결과가 없어 기존 routing cycle time을 사용합니다"]
    assert breakdowns[0]["skipped_actions"][0]["reason"] == "NO_PROFILE_ACTION"


def test_scenario_step_actions_resolves_acquire_aliases():
    content = {
        "assets": [{"id": "NC1", "name": "NX5500"}],
        "steps": [
            {
                "id": "7",
                "op_id": "OP-B02",
                "acquire": {"main": ["NC1"]},
                "routing": [{"when": "", "then": [{"next": "8"}]}],
            },
            {
                "id": "8",
                "op_id": "OP-B02",
                "action": "{{acq.main}}/CncGateway/Commands/open_door",
            },
        ],
    }

    assert scenario_step_actions(content, content["assets"]) == [
        {
            "step_id": "8",
            "op_id": "OP-B02",
            "asset": "NX5500",
            "gateway": "CncGateway",
            "action": "open_door",
            "raw_action": "{{acq.main}}/CncGateway/Commands/open_door",
        }
    ]


def test_scenario_step_actions_keeps_aliases_when_release_is_only_in_a_branch():
    content = {
        "assets": [{"id": "ANT", "name": "ANT_AMR"}],
        "steps": [
            {
                "id": "2",
                "op_id": "OP-B01",
                "acquire": {"sub2": ["ANT"]},
                "action": "CNC_DIE/HttpGateway/Queries/availableInputSlot",
                "routing": [
                    {"when": "{{res}} > 0", "then": [{"next": "4"}]},
                    {"when": "", "then": [{"release": ["{{acq.sub2}}"]}, {"wait_retry": 0}]},
                ],
            },
            {
                "id": "4",
                "op_id": "OP-B01",
                "action": "{{acq.sub2}}/RobotGateway/Commands/pick",
            },
        ],
    }

    actions = scenario_step_actions(content, content["assets"])

    assert actions[1]["asset"] == "ANT_AMR"
    assert actions[1]["action"] == "pick"


def test_scenario_1_p4r_process_mapping_calculates_cell2_times():
    adapter = P4RPayloadAdapter()
    scenario_content, _ = load_scenario_yaml("scenario_1.yaml")
    asset_rows = scenario_assets(scenario_content)
    mappings = p4r_process_mappings(scenario_content)
    actions = scenario_step_actions(scenario_content, asset_rows)
    assets = _cell2_assets_with_action_profiles()
    breakdowns = []

    process_info = adapter._build_process_info(
        "PLAT-A002",
        "MT_PLAT-A002",
        [
            _routing_with_code(
                code="LOAD",
                equipment_type="ROBOT",
                sequence=10,
                routing_cycle_time=30,
            ),
            _routing_with_code(
                code="MILL",
                equipment_type="CNC",
                sequence=20,
                routing_cycle_time=417,
            ),
            _routing_with_code(
                code="INSP",
                equipment_type="INSPECTION",
                sequence=30,
                routing_cycle_time=60,
            ),
            _routing_with_code(
                code="UNLOAD",
                equipment_type="ROBOT",
                sequence=40,
                routing_cycle_time=45,
            ),
        ],
        assets,
        [],
        mappings,
        actions,
        build_action_timing_catalog(assets),
        breakdowns,
    )

    processing_times = {
        item["PROCESS_INFO_ID"].rsplit("_", 1)[-1]: item["PROCESS_OPERATION_INFO"][0][
            "PROCESSING_TIME"
        ]
        for item in process_info
    }

    assert processing_times == {
        "LOAD": "735",
        "MILL": "417",
        "INSP": "780",
        "UNLOAD": "655",
    }
    assert {mapping["process_code"] for mapping in mappings} == {
        "LOAD",
        "MILL",
        "UNLOAD",
        "INSP",
    }
    assert next(item for item in breakdowns if item["process_code"] == "MILL")["mode"] == (
        "ROUTING_CYCLE"
    )
    assert (
        next(item for item in breakdowns if item["process_code"] == "INSP")["action_profile_sec"]
        == 780
    )


def test_build_process_info_uses_one_based_proc_num():
    adapter = P4RPayloadAdapter()
    process_info = adapter._build_process_info(
        "PLAT-A002",
        "MT_PLAT-A002",
        [
            _routing_with_code(
                code="LOAD",
                equipment_type="FEEDER",
                sequence=10,
                routing_cycle_time=30,
            ),
            _routing_with_code(
                code="MILL",
                equipment_type="CNC",
                sequence=20,
                routing_cycle_time=417,
            ),
            _routing_with_code(
                code="UNLOAD",
                equipment_type="FEEDER",
                sequence=30,
                routing_cycle_time=30,
            ),
        ],
        {"FEEDER": _feeder_asset(), "NX5500": _asset()},
    )

    assert [
        (
            item["CONSUMED_MATERIAL_INFO"][0]["PROC_NUM"],
            item["PRODUCED_MATERIAL_INFO"][0]["PROC_NUM"],
        )
        for item in process_info
    ] == [("1", "2"), ("2", "3"), ("3", "4")]


def test_build_type_sections_adds_feeder_input_output_buffers():
    adapter = P4RPayloadAdapter()
    machine_types, buffer_types, _, _ = adapter._build_type_sections({"FEEDER": _feeder_asset()})

    assert machine_types == [
        {
            "MACHINE_TYPE_ID": "FEEDER_TYPE",
            "RESOURCE_TYPE": "FEEDER",
            "CAPACITY": "1",
            "MEAN_TIME_TO_REPAIR": "999999",
            "MEAN_TIME_BETWEEN_FAILURE": "99999999",
        }
    ]
    assert buffer_types == [
        {
            "BUFFER_TYPE_ID": "BT_FEEDER_IN",
            "RESOURCE_TYPE": "BUFFER",
            "CAPACITY": "10",
        },
        {
            "BUFFER_TYPE_ID": "BT_FEEDER_OUT",
            "RESOURCE_TYPE": "BUFFER",
            "CAPACITY": "10",
        },
    ]


def test_build_type_sections_adds_qcm_as_machine_type():
    adapter = P4RPayloadAdapter()
    machine_types, buffer_types, mm_types, mhr_types = adapter._build_type_sections(
        {"EQUATOR_01": _qcm_asset()}
    )

    assert machine_types == [
        {
            "MACHINE_TYPE_ID": "QCM_EQUATOR",
            "RESOURCE_TYPE": "QUALITY_CONTROLL_MACHINE",
            "CAPACITY": "1",
            "MEAN_TIME_TO_REPAIR": "12000",
            "MEAN_TIME_BETWEEN_FAILURE": "99999999",
        }
    ]
    assert buffer_types == []
    assert mm_types == []
    assert mhr_types == []


def test_build_type_sections_uses_shared_rack_capacity():
    adapter = P4RPayloadAdapter()
    machine_types, buffer_types, mm_types, mhr_types = adapter._build_type_sections(
        {"RACK_01": _rack_asset()}
    )

    assert machine_types == []
    assert buffer_types == [
        {
            "BUFFER_TYPE_ID": "BT_RACK_01",
            "RESOURCE_TYPE": "BUFFER",
            "CAPACITY": "6",
        }
    ]
    assert mm_types == []
    assert mhr_types == []


def test_build_instances_counts_shared_rack_occupied_slots():
    adapter = P4RPayloadAdapter()
    _, buffer_instances, _, _ = adapter._build_instances(
        "PLAT-A002",
        "MT_PLAT-A002",
        {"RACK_01": _rack_asset()},
        [
            {
                "PROCESS_INFO_ID": "PP_PLAT-A002_UNLOAD",
                "PROCESS_OPERATION_INFO": [
                    {"PROCESS_OPERATION_INFO_ID": "OR_PLAT-A002_UNLOAD_RACK_01"}
                ],
            }
        ],
    )

    assert buffer_instances == [
        {
            "BUFFER_INSTANCE_ID": "RACK_01",
            "BUFFER_TYPE_ID": "BT_RACK_01",
            "WORK_IN_PROCESS_STATUS": [
                {
                    "WORK_IN_PROCESS_STATUS_ID": "WIPBF_RACK_01",
                    "FINISHED_OPERATION_INFO_ID": "OR_PLAT-A002_UNLOAD_RACK_01",
                    "MATERIAL_ID": "MT_PLAT-A002",
                    "WORK_IN_PROCESS_NUM": "3",
                }
            ],
        }
    ]


def test_build_instances_adds_feeder_buffer_counts():
    adapter = P4RPayloadAdapter()
    process_info = [
        {
            "PROCESS_INFO_ID": "PP_PLAT-A002_LOAD",
            "PROCESS_OPERATION_INFO": [{"PROCESS_OPERATION_INFO_ID": "OR_PLAT-A002_LOAD_FEEDER"}],
        },
        {
            "PROCESS_INFO_ID": "PP_PLAT-A002_UNLOAD",
            "PROCESS_OPERATION_INFO": [{"PROCESS_OPERATION_INFO_ID": "OR_PLAT-A002_UNLOAD_FEEDER"}],
        },
    ]
    machine_instances, buffer_instances, _, _ = adapter._build_instances(
        "PLAT-A002",
        "MT_PLAT-A002",
        {"FEEDER": _feeder_asset()},
        process_info,
    )

    assert machine_instances[0]["MACHINE_INSTANCE_ID"] == "FEEDER"
    assert buffer_instances == [
        {
            "BUFFER_INSTANCE_ID": "FEEDER_IN",
            "BUFFER_TYPE_ID": "BT_FEEDER_IN",
            "WORK_IN_PROCESS_STATUS": [
                {
                    "WORK_IN_PROCESS_STATUS_ID": "WIPBF_FEEDER_IN",
                    "FINISHED_OPERATION_INFO_ID": "",
                    "MATERIAL_ID": "MT_PLAT-A002",
                    "WORK_IN_PROCESS_NUM": "7",
                }
            ],
        },
        {
            "BUFFER_INSTANCE_ID": "FEEDER_OUT",
            "BUFFER_TYPE_ID": "BT_FEEDER_OUT",
            "WORK_IN_PROCESS_STATUS": [
                {
                    "WORK_IN_PROCESS_STATUS_ID": "WIPBF_FEEDER_OUT",
                    "FINISHED_OPERATION_INFO_ID": "OR_PLAT-A002_UNLOAD_FEEDER",
                    "MATERIAL_ID": "MT_PLAT-A002",
                    "WORK_IN_PROCESS_NUM": "3",
                }
            ],
        },
    ]


def test_build_instances_adds_qcm_as_machine_instance():
    adapter = P4RPayloadAdapter()
    traces = []
    machine_instances, buffer_instances, mm_instances, mhr_instances = adapter._build_instances(
        "PLAT-A002",
        "MT_PLAT-A002",
        {"EQUATOR_01": _qcm_asset()},
        [],
        traces,
    )

    assert machine_instances[0]["MACHINE_INSTANCE_ID"] == "EQUATOR_01"
    assert machine_instances[0]["MACHINE_TYPE_ID"] == "QCM_EQUATOR"
    assert machine_instances[0]["FAILURE_STATUS"][0]["FAILURE_TYPE"] == "NONE"
    assert traces[0]["resource_type"] == "QUALITY_CONTROLL_MACHINE"
    assert buffer_instances == []
    assert mm_instances == []
    assert mhr_instances == []


def test_build_instances_maps_qcm_error_failure():
    adapter = P4RPayloadAdapter()
    machine_instances, _, _, _ = adapter._build_instances(
        "PLAT-A002",
        "MT_PLAT-A002",
        {
            "EQUATOR_01": _machine_asset_with_status(
                asset_id="EQUATOR_01",
                resource_type="QCM",
                gateway="RobotGateway",
                status={"status": "ERROR", "error": "measurement alarm"},
            )
        },
        [],
    )

    failure_status = machine_instances[0]["FAILURE_STATUS"][0]
    assert failure_status["FAILURE_TYPE"] == "QCM_ERROR"
    assert failure_status["REMAINING_REPAIR_TIME"] == "600"


def test_build_process_info_prefers_qcm_asset_for_inspection_process():
    adapter = P4RPayloadAdapter()
    process_info = adapter._build_process_info(
        "PLAT-A002",
        "MT_PLAT-A002",
        [
            _routing_with_code(
                code="INSP",
                equipment_type="ROBOT",
                sequence=40,
                routing_cycle_time=300,
            )
        ],
        {"DH400": _asset(), "EQUATOR_01": _qcm_asset()},
    )

    operation = process_info[0]["PROCESS_OPERATION_INFO"][0]
    assert operation["MACHINE_TYPE_ID"] == "QCM_EQUATOR"
    assert operation["PROCESS_OPERATION_INFO_ID"] == "OR_PLAT-A002_INSP_EQUATOR_01"


def test_build_instances_sets_none_failure_status_by_default():
    adapter = P4RPayloadAdapter()
    machine_instances, _, _, _ = adapter._build_instances(
        "PLAT-A002",
        "MT_PLAT-A002",
        {"NX5500": _machine_asset_with_status(status={"status": "IDLE"})},
        [],
    )

    failure_status = machine_instances[0]["FAILURE_STATUS"][0]
    assert failure_status["FAILURE_TYPE"] == "NONE"
    assert failure_status["REMAINING_REPAIR_TIME"] == "0"


def test_build_instances_maps_disconnected_machine_failure():
    adapter = P4RPayloadAdapter()
    traces = []
    machine_instances, _, _, _ = adapter._build_instances(
        "PLAT-A002",
        "MT_PLAT-A002",
        {"NX5500": _machine_asset_with_status(is_connected=False)},
        [],
        traces,
    )

    failure_status = machine_instances[0]["FAILURE_STATUS"][0]
    assert failure_status["FAILURE_TYPE"] == "DISCONNECTED"
    assert failure_status["REMAINING_REPAIR_TIME"] == "300"
    assert traces[0]["matchedRule"] == "disconnected"


def test_build_instances_maps_cnc_alarm_failure():
    adapter = P4RPayloadAdapter()
    traces = []
    machine_instances, _, _, _ = adapter._build_instances(
        "PLAT-A002",
        "MT_PLAT-A002",
        {
            "NX5500": _machine_asset_with_status(
                status={"status": "ALARM", "alarm": "spindle alarm"}
            )
        },
        [],
        traces,
    )

    failure_status = machine_instances[0]["FAILURE_STATUS"][0]
    assert failure_status["FAILURE_TYPE"] == "CNC_ALARM"
    assert failure_status["REMAINING_REPAIR_TIME"] == "600"
    assert traces[0]["rawMessage"] == "spindle alarm"


def test_build_instances_maps_feeder_robot_gateway_error():
    adapter = P4RPayloadAdapter()
    machine_instances, _, _, _ = adapter._build_instances(
        "PLAT-A002",
        "MT_PLAT-A002",
        {
            "FEEDER": _machine_asset_with_status(
                asset_id="FEEDER",
                resource_type="FEEDER",
                gateway="RobotGateway",
                status={"status": "ERROR", "error": "loader jam"},
            )
        },
        [],
    )

    failure_status = machine_instances[0]["FAILURE_STATUS"][0]
    assert failure_status["FAILURE_TYPE"] == "ROBOT_ERROR"
    assert failure_status["REMAINING_REPAIR_TIME"] == "600"


def test_load_p4r_failure_rules_falls_back_when_json_is_invalid(tmp_path):
    bad_rules_path = tmp_path / "p4r_failure_rules.json"
    bad_rules_path.write_text("{", encoding="utf-8")

    rule_set = load_p4r_failure_rules(bad_rules_path)
    interpreted = rule_set.interpret(
        asset_id="NX5500",
        resource_type="CNC",
        status={"status": "ALARM"},
    )

    assert rule_set.source == "built-in-default"
    assert rule_set.warnings
    assert interpreted.failure_type == "CNC_ALARM"


def test_load_p4r_failure_rules_supports_custom_json_rule(tmp_path):
    rules_path = tmp_path / "p4r_failure_rules.json"
    rules_path.write_text(
        """
{
  "default": {"failureType": "NONE", "remainingRepairTime": 0},
  "rules": [
    {
      "id": "blocked_status",
      "priority": 5,
      "resourceTypes": ["CNC"],
      "when": {"field": "status", "equals": "BLOCKED"},
      "result": {"failureType": "RESOURCE_BLOCKED", "remainingRepairTime": 120}
    }
  ]
}
""",
        encoding="utf-8",
    )

    rule_set = load_p4r_failure_rules(rules_path)
    interpreted = rule_set.interpret(
        asset_id="NX5500",
        resource_type="CNC",
        status={"status": "BLOCKED"},
    )

    assert interpreted.failure_type == "RESOURCE_BLOCKED"
    assert interpreted.remaining_repair_time == 120
