#!/usr/bin/env python3
"""Add Cell 1 digital-twin simulation profile metadata to assets.aasx.

The AASX file is a zip package. This script updates aasx/data.xml directly:
- adds one DtSimulationProfile submodel per target asset
- adds missing on-demand Queries for runtime DT payload values
- duplicates P4R runtime query properties into Status without removing Queries
- keeps unrelated AAS/package files unchanged
"""

from __future__ import annotations

import argparse
import shutil
import zipfile
from datetime import datetime
from pathlib import Path
import xml.etree.ElementTree as ET


AAS_NS = "https://admin-shell.io/aas/3/0"
ET.register_namespace("aas", AAS_NS)


def tag(name: str) -> str:
    return f"{{{AAS_NS}}}{name}"


TARGET_PROFILES = {
    "NX5500": {
        "dt_resource_type": ("xs:string", "CNC"),
        "dt_type_id": ("xs:string", "CNC_NX5500"),
        "capacity": ("xs:int", "1"),
        "mean_time_to_repair": ("xs:int", "12000"),
        "mean_time_between_failure": ("xs:int", "99999999"),
        "setup_change_time_min": ("xs:int", "5"),
        "current_setup_id": ("xs:string", "TS-PLT-001"),
        "loading_type": ("xs:string", "pallet_single"),
        "amr_transport_qty": ("xs:int", "1"),
        "exchange_time_sec": ("xs:int", "0"),
        "load_unload_time_sec": ("xs:int", "30"),
    },
    "ANT_AMR": {
        "dt_resource_type": ("xs:string", "MM"),
        "dt_type_id": ("xs:string", "MM_ANT_AMR"),
        "capacity": ("xs:int", "1"),
        "handling_batch_size": ("xs:int", "1"),
        "push_pull": ("xs:string", "PULL"),
        "loading_time_sec": ("xs:int", "45"),
        "unloading_time_sec": ("xs:int", "45"),
        "operation_speed": ("xs:int", "80"),
        "transportation_speed": ("xs:int", "70"),
        "turn_speed": ("xs:int", "35"),
        "move_speed": ("xs:int", "1000"),
        "battery_capacity": ("xs:int", "100"),
        "power_to_charge_limit": ("xs:int", "15"),
        "mean_time_to_repair": ("xs:int", "999999"),
        "mean_time_between_failure": ("xs:int", "999999"),
    },
    "UR_ROBOT": {
        "dt_resource_type": ("xs:string", "CR"),
        "dt_type_id": ("xs:string", "CR_UR_ROBOT"),
        "capacity": ("xs:int", "1"),
        "mean_time_to_repair": ("xs:int", "999999"),
        "mean_time_between_failure": ("xs:int", "999999"),
    },
    "FEEDER": {
        "dt_resource_type": ("xs:string", "FEEDER"),
        "dt_type_id": ("xs:string", "FEEDER_TYPE"),
        "capacity": ("xs:int", "1"),
        "handling_batch_size": ("xs:int", "1"),
        "loading_time_sec": ("xs:int", "45"),
        "unloading_time_sec": ("xs:int", "45"),
        "mean_time_to_repair": ("xs:int", "999999"),
        "mean_time_between_failure": ("xs:int", "99999999"),
    },
    "CNC_DIE": {
        "dt_resource_type": ("xs:string", "BUFFER"),
        "dt_type_id": ("xs:string", "BT_CNC_DIE"),
        "capacity": ("xs:int", "2"),
        "input_slot_capacity": ("xs:int", "1"),
        "output_slot_capacity": ("xs:int", "1"),
    },
}


ROBOT_QUERY_ADDS = {
    "ANT_AMR": [
        ("status", "xs:string", "", "status"),
        ("agvPositionX", "xs:double", "0.0", "agvPosition.x"),
        ("agvPositionY", "xs:double", "0.0", "agvPosition.y"),
        ("agvPositionTheta", "xs:double", "0.0", "agvPosition.theta"),
        ("batteryCharge", "xs:double", "0.0", "batteryState.batteryCharge"),
        ("velocity", "xs:double", "0.0", "velocity"),
    ],
    "UR_ROBOT": [
        ("status", "xs:string", "", "status"),
        ("batteryCharge", "xs:double", "0.0", "batteryState.batteryCharge"),
        ("manipulatorState", "xs:string", "", "manipulatorState"),
    ],
    "FEEDER": [
        ("status", "xs:string", "", "status"),
    ],
}


HTTP_QUERY_ADDS = {
    "CNC_DIE": [
        ("allSlots", "xs:string", "/devices/{deviceId}/slots", ""),
        ("occupiedInputSlot", "xs:string", "/devices/{deviceId}/slots/occupied/first?type=INPUT_ONLY&content=material", "slot_id"),
        ("occupiedOutputSlot", "xs:string", "/devices/{deviceId}/slots/occupied/first?type=OUTPUT_ONLY&content=product", "slot_id"),
    ],
}


STATUS_DUPLICATE_FROM_QUERIES = {
    "NX5500": {
        "gateway": "CncGateway",
        "properties": [
            "is_door_open",
            "is_door_closed",
            "is_vise_open",
            "is_vise_closed",
            "is_M20",
        ],
    },
    "ANT_AMR": {
        "gateway": "RobotGateway",
        "properties": [
            "availableInputSlot",
            "occupiedInputSlot",
            "availableOutputSlot",
            "occupiedOutputSlot",
            "status",
            "agvPositionX",
            "agvPositionY",
            "agvPositionTheta",
            "batteryCharge",
            "velocity",
        ],
    },
    "UR_ROBOT": {
        "gateway": "RobotGateway",
        "properties": [
            "occupiedInputSlot",
            "availableOutputSlot",
            "availableInputSlot",
            "status",
            "batteryCharge",
            "manipulatorState",
        ],
    },
    "FEEDER": {
        "gateway": "RobotGateway",
        "properties": [
            "loaderCount",
            "unloaderCount",
            "status",
        ],
    },
    "CNC_DIE": {
        "gateway": "HttpGateway",
        "properties": [
            "availableInputSlot",
            "availableOutputSlot",
            "allSlots",
            "occupiedInputSlot",
            "occupiedOutputSlot",
        ],
    },
}


def child(parent: ET.Element, name: str, text: str | None = None) -> ET.Element:
    el = ET.SubElement(parent, tag(name))
    if text is not None:
        el.text = text
    return el


def extension(name: str, value_type: str, value: str) -> ET.Element:
    ext = ET.Element(tag("extension"))
    child(ext, "name", name)
    child(ext, "valueType", value_type)
    if value != "":
        child(ext, "value", value)
    else:
        child(ext, "value")
    return ext


def property_el(
    id_short: str,
    value_type: str,
    value: str,
    ext_values: dict[str, tuple[str, str]] | None = None,
) -> ET.Element:
    prop = ET.Element(tag("property"))
    if ext_values:
        exts = child(prop, "extensions")
        for key, (vt, val) in ext_values.items():
            exts.append(extension(key, vt, val))
    child(prop, "idShort", id_short)
    child(prop, "valueType", value_type)
    if value != "":
        child(prop, "value", value)
    else:
        child(prop, "value")
    return prop


def reference_el(identifier: str) -> ET.Element:
    ref = ET.Element(tag("reference"))
    child(ref, "type", "ModelReference")
    keys = child(ref, "keys")
    key = child(keys, "key")
    child(key, "type", "Submodel")
    child(key, "value", identifier)
    return ref


def submodel_profile(asset_id: str, values: dict[str, tuple[str, str]]) -> ET.Element:
    sm = ET.Element(tag("submodel"))
    child(sm, "idShort", "DtSimulationProfile")
    child(sm, "id", f"https://example.com/ids/aas/{asset_id}/DtSimulationProfile")
    child(sm, "kind", "Instance")
    semantic = child(sm, "semanticId")
    child(semantic, "type", "ExternalReference")
    keys = child(semantic, "keys")
    key = child(keys, "key")
    child(key, "type", "GlobalReference")
    child(key, "value", "https://kitech.re.kr/ids/sm/DtSimulationProfile/1/0")
    elements = child(sm, "submodelElements")
    for name, (vt, val) in values.items():
        elements.append(property_el(name, vt, val))
    return sm


def find_aas(root: ET.Element, asset_id: str) -> ET.Element | None:
    for aas in root.findall(f".//{tag('assetAdministrationShell')}"):
        id_short = aas.findtext(tag("idShort"))
        if id_short == asset_id:
            return aas
    return None


def find_submodel(root: ET.Element, sm_id: str) -> ET.Element | None:
    for sm in root.findall(f".//{tag('submodel')}"):
        if sm.findtext(tag("id")) == sm_id:
            return sm
    return None


def aas_submodel_refs(aas: ET.Element) -> list[str]:
    return [
        (value.text or "").strip()
        for value in aas.findall(f".//{tag('submodels')}/{tag('reference')}/{tag('keys')}/{tag('key')}/{tag('value')}")
        if (value.text or "").strip()
    ]


def find_asset_gateway_submodel(root: ET.Element, asset_id: str, gateway_id_short: str) -> ET.Element | None:
    aas = find_aas(root, asset_id)
    if aas is None:
        return None
    for sm_id in aas_submodel_refs(aas):
        sm = find_submodel(root, sm_id)
        if sm is not None and sm.findtext(tag("idShort")) == gateway_id_short:
            return sm
    return None


def ensure_submodels_container(aas: ET.Element) -> ET.Element:
    submodels = aas.find(tag("submodels"))
    if submodels is None:
        submodels = child(aas, "submodels")
    return submodels


def has_ref(aas: ET.Element, sm_id: str) -> bool:
    return any(
        (value.text or "").strip() == sm_id
        for value in aas.findall(f".//{tag('submodels')}/{tag('reference')}/{tag('keys')}/{tag('key')}/{tag('value')}")
    )


def collection(sm: ET.Element, name: str) -> ET.Element | None:
    for coll in sm.findall(f"./{tag('submodelElements')}/{tag('submodelElementCollection')}"):
        if coll.findtext(tag("idShort")) == name:
            return coll
    return None


def ensure_collection(sm: ET.Element, name: str) -> ET.Element:
    elements = sm.find(tag("submodelElements"))
    if elements is None:
        elements = child(sm, "submodelElements")
    coll = collection(sm, name)
    if coll is None:
        coll = child(elements, "submodelElementCollection")
        child(coll, "idShort", name)
        child(coll, "value")
    value = coll.find(tag("value"))
    if value is None:
        value = child(coll, "value")
    return value


def has_collection_property(sm: ET.Element, collection_name: str, prop_name: str) -> bool:
    coll = collection(sm, collection_name)
    if coll is None:
        return False
    return any(
        prop.findtext(tag("idShort")) == prop_name
        for prop in coll.findall(f"./{tag('value')}/{tag('property')}")
    )


def normalize_query_property(prop: ET.Element, value_type: str, default_value: str) -> bool:
    changed = False
    vt_el = prop.find(tag("valueType"))
    if vt_el is not None and (vt_el.text or "").strip() != value_type:
        vt_el.text = value_type
        changed = True
    val_el = prop.find(tag("value"))
    if val_el is None:
        val_el = child(prop, "value")
        changed = True
    if value_type in {"xs:double", "xs:float"} and (val_el.text or "").strip() == "":
        val_el.text = default_value or "0.0"
        changed = True
    if value_type in {"xs:int", "xs:integer"} and (val_el.text or "").strip() == "":
        val_el.text = default_value or "0"
        changed = True
    # These ad-hoc DT snapshot queries do not need order correlation, and an
    # empty xs:boolean extension creates BaSyx reader warnings.
    exts = prop.find(tag("extensions"))
    if exts is not None:
        for ext in list(exts.findall(tag("extension"))):
            if ext.findtext(tag("name")) == "orderCorrelated":
                exts.remove(ext)
                changed = True
        if len(list(exts)) == 0:
            prop.remove(exts)
            changed = True
    return changed


def get_collection_property(sm: ET.Element, collection_name: str, prop_name: str) -> ET.Element | None:
    coll = collection(sm, collection_name)
    if coll is None:
        return None
    for prop in coll.findall(f"./{tag('value')}/{tag('property')}"):
        if prop.findtext(tag("idShort")) == prop_name:
            return prop
    return None


def add_robot_query(sm: ET.Element, name: str, value_type: str, value: str, value_path: str) -> str | None:
    endpoint = ""
    existing = get_collection_property(sm, "Queries", name)
    if existing is not None:
        return "normalized" if normalize_query_property(existing, value_type, value) else None
    value = ensure_collection(sm, "Queries")
    value.append(
        property_el(
            name,
            value_type,
            value,
            {
                "endpoint": ("xs:string", endpoint),
                "valuePath": ("xs:string", value_path),
                "logic": ("xs:string", "direct"),
                "valueMap": ("xs:string", ""),
            },
        )
    )
    return "added"


def add_http_query(sm: ET.Element, name: str, value_type: str, endpoint: str, value_path: str) -> str | None:
    existing = get_collection_property(sm, "Queries", name)
    if existing is not None:
        return "normalized" if normalize_query_property(existing, value_type, "") else None
    value = ensure_collection(sm, "Queries")
    value.append(
        property_el(
            name,
            value_type,
            "",
            {
                "endpoint": ("xs:string", endpoint),
                "valuePath": ("xs:string", value_path),
                "logic": ("xs:string", "direct"),
                "valueMap": ("xs:string", ""),
            },
        )
    )
    return "added"


def duplicate_query_to_status(sm: ET.Element, prop_name: str) -> str:
    query_prop = get_collection_property(sm, "Queries", prop_name)
    if query_prop is None:
        return "missing-query"
    if get_collection_property(sm, "Status", prop_name) is not None:
        return "exists"
    status_value = ensure_collection(sm, "Status")
    status_value.append(ET.fromstring(ET.tostring(query_prop, encoding="utf-8")))
    return "added"


def apply_updates(xml_bytes: bytes) -> tuple[bytes, list[str]]:
    root = ET.fromstring(xml_bytes)
    changes: list[str] = []
    submodels_root = root.find(tag("submodels"))
    if submodels_root is None:
        raise RuntimeError("aas:submodels container not found")

    for asset_id, values in TARGET_PROFILES.items():
        aas = find_aas(root, asset_id)
        if aas is None:
            changes.append(f"missing asset: {asset_id}")
            continue
        sm_id = f"https://example.com/ids/aas/{asset_id}/DtSimulationProfile"
        if find_submodel(root, sm_id) is None:
            submodels_root.append(submodel_profile(asset_id, values))
            changes.append(f"added submodel: {asset_id}/DtSimulationProfile")
        if not has_ref(aas, sm_id):
            ensure_submodels_container(aas).append(reference_el(sm_id))
            changes.append(f"added submodel ref: {asset_id} -> DtSimulationProfile")

    for asset_id, queries in ROBOT_QUERY_ADDS.items():
        sm = find_submodel(root, f"https://example.com/ids/aas/{asset_id}/RobotGateway")
        if sm is None:
            changes.append(f"missing RobotGateway: {asset_id}")
            continue
        for query in queries:
            result = add_robot_query(sm, *query)
            if result:
                changes.append(f"{result} RobotGateway query: {asset_id}/{query[0]}")

    for asset_id, queries in HTTP_QUERY_ADDS.items():
        sm = find_submodel(root, f"https://example.com/ids/aas/{asset_id}/HttpGateway")
        if sm is None:
            changes.append(f"missing HttpGateway: {asset_id}")
            continue
        for query in queries:
            result = add_http_query(sm, *query)
            if result:
                changes.append(f"{result} HttpGateway query: {asset_id}/{query[0]}")

    for asset_id, spec in STATUS_DUPLICATE_FROM_QUERIES.items():
        gateway_name = spec["gateway"]
        sm = find_asset_gateway_submodel(root, asset_id, gateway_name)
        if sm is None:
            changes.append(f"missing {gateway_name}: {asset_id}")
            continue
        for prop_name in spec["properties"]:
            result = duplicate_query_to_status(sm, prop_name)
            if result == "added":
                changes.append(f"added {gateway_name} status from query: {asset_id}/{prop_name}")
            elif result == "missing-query":
                changes.append(f"missing source query for status: {asset_id}/{gateway_name}/{prop_name}")

    return ET.tostring(root, encoding="utf-8", xml_declaration=False), changes


def update_aasx(path: Path, dry_run: bool) -> list[str]:
    with zipfile.ZipFile(path, "r") as zin:
        xml_bytes = zin.read("aasx/data.xml")
        new_xml, changes = apply_updates(xml_bytes)
        if dry_run:
            return changes
        backup_dir = path.parent.parent / "aasx_backup"
        backup_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"{path.name}.{stamp}.bak"
        shutil.copy2(path, backup_path)
        tmp_path = path.with_suffix(path.suffix + ".tmp")
        with zipfile.ZipFile(tmp_path, "w") as zout:
            for item in zin.infolist():
                data = new_xml if item.filename == "aasx/data.xml" else zin.read(item.filename)
                zi = zipfile.ZipInfo(item.filename, item.date_time)
                zi.comment = item.comment
                zi.extra = item.extra
                zi.internal_attr = item.internal_attr
                zi.external_attr = item.external_attr
                zi.create_system = item.create_system
                zi.compress_type = item.compress_type
                zout.writestr(zi, data)
        tmp_path.replace(path)
        changes.append(f"backup: {backup_path}")
        return changes


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("aasx_path", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    changes = update_aasx(args.aasx_path, args.dry_run)
    for change in changes:
        print(change)


if __name__ == "__main__":
    main()
