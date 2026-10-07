#!/usr/bin/env python3
"""Add Cell2 DtSimulationProfile and P4RActionTimingProfile submodels to assets.aasx."""

from __future__ import annotations

import argparse
import shutil
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path
from xml.etree import ElementTree as ET

AAS_NS = "https://admin-shell.io/aas/3/0"
DATA_XML = "aasx/data.xml"
DT_PROFILE_SEMANTIC_ID = "https://kitech.re.kr/ids/sm/DtSimulationProfile/1/0"
P4R_TIMING_SEMANTIC_ID = "https://kitech.re.kr/ids/sm/P4RActionTimingProfile/1/0"
DEFAULT_AASX = Path(
    "/Users/beomhwanham/Desktop/kitech/robot/middleware/am-middleware/aasx/assets.aasx"
)

ET.register_namespace("aas", AAS_NS)


CELL2_DT_PROFILES = {
    "DH400": [
        ("dt_resource_type", "xs:string", "CNC"),
        ("dt_type_id", "xs:string", "CNC_DH400"),
        ("capacity", "xs:int", 1),
        ("mean_time_to_repair", "xs:int", 12000),
        ("mean_time_between_failure", "xs:int", 99999999),
        ("setup_change_time_min", "xs:int", 5),
        ("loading_type", "xs:string", "single_piece"),
        ("amr_transport_qty", "xs:int", 1),
        ("exchange_time_sec", "xs:int", 0),
        ("load_unload_time_sec", "xs:int", 0),
    ],
    "DOOSAN_MOMA": [
        ("dt_resource_type", "xs:string", "MM"),
        ("dt_type_id", "xs:string", "MM_DOOSAN_MOMA"),
        ("capacity", "xs:int", 1),
        ("handling_batch_size", "xs:int", 1),
        ("push_pull", "xs:string", "PULL"),
        ("loading_time_sec", "xs:int", 0),
        ("unloading_time_sec", "xs:int", 0),
        ("operation_speed", "xs:int", 80),
        ("transportation_speed", "xs:int", 70),
        ("turn_speed", "xs:int", 35),
        ("move_speed", "xs:int", 1000),
        ("battery_capacity", "xs:int", 100),
        ("power_to_charge_limit", "xs:int", 15),
        ("mean_time_to_repair", "xs:int", 999999),
        ("mean_time_between_failure", "xs:int", 999999),
    ],
    "EQUATOR_01": [
        ("dt_resource_type", "xs:string", "QCM"),
        ("dt_type_id", "xs:string", "QCM_EQUATOR"),
        ("capacity", "xs:int", 1),
        ("mean_time_to_repair", "xs:int", 12000),
        ("mean_time_between_failure", "xs:int", 99999999),
    ],
    "RACK_01": [
        ("dt_resource_type", "xs:string", "BUFFER"),
        ("dt_type_id", "xs:string", "BT_RACK_01"),
        ("capacity", "xs:int", 6),
        ("slot_mode", "xs:string", "SHARED"),
    ],
}


CELL2_ACTIONS = {
    "DH400": [
        ("ClampVise", "ModbusGateway", 10, "PROCESS_INTERNAL", True),
        ("UnClampVise", "ModbusGateway", 10, "PROCESS_INTERNAL", True),
        ("excute_main_program", "CncGateway", 5, "PROCESS_INTERNAL", True),
    ],
    "DOOSAN_MOMA": [
        ("move", "RobotGateway", 60, "PROCESS_INTERNAL", True),
        ("pick", "RobotGateway", 120, "PROCESS_INTERNAL", True),
        ("place", "RobotGateway", 120, "PROCESS_INTERNAL", True),
        ("detect_cnc", "RobotGateway", 40, "PROCESS_INTERNAL", True),
        ("open_cnc", "RobotGateway", 120, "PROCESS_INTERNAL", True),
        ("tray1_to_cnc", "RobotGateway", 120, "PROCESS_INTERNAL", True),
        ("cnc_to_tray2", "RobotGateway", 120, "PROCESS_INTERNAL", True),
        ("close_cnc", "RobotGateway", 120, "PROCESS_INTERNAL", True),
        ("start_process", "RobotGateway", 60, "PROCESS_INTERNAL", True),
    ],
    "EQUATOR_01": [
        ("close_clamp", "RobotGateway", 60, "PROCESS_INTERNAL", True),
        ("measure", "RobotGateway", 300, "PROCESS_INTERNAL", True),
        ("open_clamp", "RobotGateway", 60, "PROCESS_INTERNAL", True),
    ],
    "RACK_01": [
        ("input", "HttpGateway", 5, "PROCESS_INTERNAL", True),
        ("output", "HttpGateway", 5, "PROCESS_INTERNAL", True),
    ],
}


def q(tag: str) -> str:
    return f"{{{AAS_NS}}}{tag}"


def elem(tag: str, text: object | None = None) -> ET.Element:
    node = ET.Element(q(tag))
    if text is not None:
        node.text = str(text).lower() if isinstance(text, bool) else str(text)
    return node


def prop(id_short: str, value_type: str, value: object) -> ET.Element:
    node = elem("property")
    node.append(elem("idShort", id_short))
    node.append(elem("valueType", value_type))
    node.append(elem("value", value))
    return node


def collection(id_short: str, children: list[ET.Element]) -> ET.Element:
    node = elem("submodelElementCollection")
    node.append(elem("idShort", id_short))
    value = elem("value")
    value.extend(children)
    node.append(value)
    return node


def semantic_reference(value: str) -> ET.Element:
    semantic_id = elem("semanticId")
    semantic_id.append(elem("type", "ExternalReference"))
    keys = elem("keys")
    key = elem("key")
    key.append(elem("type", "GlobalReference"))
    key.append(elem("value", value))
    keys.append(key)
    semantic_id.append(keys)
    return semantic_id


def submodel_reference(value: str) -> ET.Element:
    reference = elem("reference")
    reference.append(elem("type", "ModelReference"))
    keys = elem("keys")
    key = elem("key")
    key.append(elem("type", "Submodel"))
    key.append(elem("value", value))
    keys.append(key)
    reference.append(keys)
    return reference


def submodel(
    asset_id: str, id_short: str, semantic_id: str, elements: list[ET.Element]
) -> ET.Element:
    node = elem("submodel")
    node.append(elem("idShort", id_short))
    node.append(elem("id", f"https://example.com/ids/aas/{asset_id}/{id_short}"))
    node.append(elem("kind", "Instance"))
    node.append(semantic_reference(semantic_id))
    submodel_elements = elem("submodelElements")
    submodel_elements.extend(elements)
    node.append(submodel_elements)
    return node


def dt_simulation_profile(asset_id: str) -> ET.Element:
    properties = [
        prop(id_short, value_type, value)
        for id_short, value_type, value in CELL2_DT_PROFILES[asset_id]
    ]
    return submodel(asset_id, "DtSimulationProfile", DT_PROFILE_SEMANTIC_ID, properties)


def p4r_action_timing_profile(asset_id: str) -> ET.Element:
    action_nodes: list[ET.Element] = []
    for action_id, gateway, duration_sec, ownership, contributes in CELL2_ACTIONS[asset_id]:
        action_nodes.append(
            collection(
                action_id,
                [
                    prop("gateway", "xs:string", gateway),
                    prop("defaultDurationSec", "xs:int", duration_sec),
                    prop("timeOwnership", "xs:string", ownership),
                    prop("canContributeToRoutingCycleTime", "xs:boolean", contributes),
                ],
            )
        )
    return submodel(
        asset_id,
        "P4RActionTimingProfile",
        P4R_TIMING_SEMANTIC_ID,
        [
            prop("profileVersion", "xs:string", "1.0"),
            collection(
                "TimingPolicy",
                [
                    prop("processingTimeOwner", "xs:string", "MES_ROUTING"),
                    prop("directP4RCalculationFromAAS", "xs:boolean", False),
                ],
            ),
            collection("Actions", action_nodes),
        ],
    )


def find_child_text(parent: ET.Element, child_name: str) -> str:
    child = parent.find(q(child_name))
    return child.text or "" if child is not None else ""


def existing_reference_values(shell: ET.Element) -> set[str]:
    values: set[str] = set()
    submodels = shell.find(q("submodels"))
    if submodels is None:
        return values
    for value in submodels.findall(f".//{q('value')}"):
        if value.text:
            values.add(value.text)
    return values


def add_shell_references(root: ET.Element, asset_id: str) -> int:
    shells = root.find(q("assetAdministrationShells"))
    if shells is None:
        raise RuntimeError("assetAdministrationShells not found")
    target_shell = None
    for shell in shells.findall(q("assetAdministrationShell")):
        if find_child_text(shell, "idShort") == asset_id:
            target_shell = shell
            break
    if target_shell is None:
        raise RuntimeError(f"AAS shell not found: {asset_id}")

    submodels = target_shell.find(q("submodels"))
    if submodels is None:
        submodels = elem("submodels")
        target_shell.append(submodels)

    added = 0
    refs = existing_reference_values(target_shell)
    for id_short in ("DtSimulationProfile", "P4RActionTimingProfile"):
        value = f"https://example.com/ids/aas/{asset_id}/{id_short}"
        if value in refs:
            continue
        submodels.append(submodel_reference(value))
        added += 1
    return added


def remove_existing_target_submodels(submodels: ET.Element) -> int:
    target_ids = {
        f"https://example.com/ids/aas/{asset_id}/{id_short}"
        for asset_id in CELL2_DT_PROFILES
        for id_short in ("DtSimulationProfile", "P4RActionTimingProfile")
    }
    removed = 0
    for node in list(submodels):
        if find_child_text(node, "id") in target_ids:
            submodels.remove(node)
            removed += 1
    return removed


def add_cell2_submodels(root: ET.Element) -> tuple[int, int]:
    submodels = root.find(q("submodels"))
    if submodels is None:
        raise RuntimeError("submodels not found")

    added_refs = 0
    for asset_id in CELL2_DT_PROFILES:
        added_refs += add_shell_references(root, asset_id)

    removed_submodels = remove_existing_target_submodels(submodels)
    for asset_id in CELL2_DT_PROFILES:
        submodels.append(dt_simulation_profile(asset_id))
        submodels.append(p4r_action_timing_profile(asset_id))
    return added_refs, removed_submodels


def write_aasx(source: Path, xml_bytes: bytes) -> Path:
    backup = source.with_name(f"{source.name}.bak-cell2-p4r-{datetime.now():%Y%m%d%H%M%S}")
    shutil.copy2(source, backup)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".aasx") as handle:
        temp_path = Path(handle.name)

    try:
        with zipfile.ZipFile(source, "r") as zin, zipfile.ZipFile(temp_path, "w") as zout:
            for info in zin.infolist():
                data = xml_bytes if info.filename == DATA_XML else zin.read(info.filename)
                zout.writestr(info, data)
        shutil.move(temp_path, source)
    finally:
        if temp_path.exists():
            temp_path.unlink()
    return backup


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--aasx", type=Path, default=DEFAULT_AASX)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    with zipfile.ZipFile(args.aasx, "r") as archive:
        xml_bytes = archive.read(DATA_XML)

    root = ET.fromstring(xml_bytes)
    added_refs, removed_submodels = add_cell2_submodels(root)
    ET.indent(root, space="  ")
    updated_xml = ET.tostring(root, encoding="utf-8", xml_declaration=True)

    if args.dry_run:
        print(f"dry-run: references_to_add={added_refs}, submodels_to_replace={removed_submodels}")
        return

    backup = write_aasx(args.aasx, updated_xml)
    print(f"updated: {args.aasx}")
    print(f"backup: {backup}")
    print(f"references_added: {added_refs}")
    print(f"submodels_replaced: {removed_submodels}")
    print(f"submodels_upserted: {len(CELL2_DT_PROFILES) * 2}")


if __name__ == "__main__":
    main()
