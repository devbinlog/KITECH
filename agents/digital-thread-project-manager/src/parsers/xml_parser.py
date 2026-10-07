"""XML parser and serializer for ISO 14649 dt_asset schema."""

import io
import re
import dataclasses
from typing import Any
from enum import Enum

import xmltodict
from xsdata.formats.dataclass.parsers import XmlParser
from xsdata.formats.dataclass.parsers.config import ParserConfig
from xsdata.formats.dataclass.context import XmlContext
from xsdata.formats.dataclass.serializers import XmlSerializer
from xsdata.formats.dataclass.serializers.config import SerializerConfig
from xsdata.utils import text

from ..models.dt_asset import DtAsset

DEFAULT_SCHEMA_VERSION = "v31"

# Parser configurations
_lenient_config = ParserConfig(fail_on_unknown_properties=False)
_lenient_context = XmlContext(element_name_generator=text.snake_case)
_lenient_parser = XmlParser(config=_lenient_config, context=_lenient_context)
_strict_parser = XmlParser()
_serializer = XmlSerializer(config=SerializerConfig(pretty_print=True))


def validate_xml(xml_content: str) -> bool:
    """Validate XML against DtAsset schema."""
    try:
        _strict_parser.parse(io.BytesIO(xml_content.encode("utf-8")), DtAsset)
        return True
    except Exception:
        return False


def parse_xml(xml_content: str, lenient: bool = True) -> DtAsset:
    """Parse XML to DtAsset dataclass."""
    parser = _lenient_parser if lenient else _strict_parser
    return parser.parse(io.BytesIO(xml_content.encode("utf-8")), DtAsset)


def serialize_to_xml(dt_asset: DtAsset) -> str:
    """Serialize DtAsset dataclass to XML string."""
    return _serializer.render(dt_asset)


def get_nested_value(data: dict[str, Any], keys: list[str]) -> Any:
    """Get nested value from dict using key path."""
    for key in keys:
        if isinstance(data, dict) and key in data:
            data = data[key]
        else:
            return None
    return data


def camel_to_snake(name: str) -> str:
    """Convert camelCase to snake_case."""
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


def dataclass_to_dict(data: Any) -> dict | list | Any:
    """Convert dataclass to dict recursively."""
    if isinstance(data, list):
        return [dataclass_to_dict(item) for item in data if item != []]
    elif dataclasses.is_dataclass(data):
        return {
            field.name: dataclass_to_dict(getattr(data, field.name))
            for field in dataclasses.fields(data)
            if getattr(data, field.name) is not None and getattr(data, field.name) != []
        }
    else:
        return data


def merge_dicts(original: dict, updates: dict) -> dict:
    """Deep merge two dicts, preferring updates for leaf values."""
    merged = {}
    all_keys = set(original.keys()) | set(updates.keys())

    for key in all_keys:
        orig_val = original.get(key)
        upd_val = updates.get(key)

        if key.startswith("@"):
            merged[key] = orig_val if orig_val is not None else upd_val
            continue

        if orig_val is None:
            merged[key] = upd_val
            continue
        if upd_val is None:
            merged[key] = orig_val
            continue

        if isinstance(orig_val, dict) and isinstance(upd_val, dict):
            merged[key] = merge_dicts(orig_val, upd_val)
        elif isinstance(orig_val, list) and isinstance(upd_val, list):
            merged[key] = [
                merge_dicts(o, u) if isinstance(o, dict) and isinstance(u, dict) else u
                for o, u in zip(orig_val, upd_val)
            ]
        else:
            merged[key] = upd_val

    return merged


def extract_dtasset_meta(xml_string: str) -> dict[str, str | None]:
    """Extract metadata from dt_asset XML."""
    doc = xmltodict.parse(
        xml_string,
        process_namespaces=True,
        namespaces={
            "http://digital-thread.re/dt_asset": None,
            "http://www.w3.org/2001/XMLSchema-instance": "xsi",
        },
        attr_prefix="@",
    )

    dt_asset = doc.get("dt_asset", {})
    elems = dt_asset.get("dt_elements")
    first_elem = elems[0] if isinstance(elems, list) else (elems or {})

    return {
        "global_asset_id": dt_asset.get("asset_global_id"),
        "asset_id": dt_asset.get("id"),
        "type": first_elem.get("@xsi:type") if isinstance(first_elem, dict) else None,
        "category": first_elem.get("category") if isinstance(first_elem, dict) else None,
        "element_id": first_elem.get("element_id") if isinstance(first_elem, dict) else None,
    }


def resolve_enum(enum_type: type[Enum], value: Any) -> Enum | None:
    """Safely convert value to enum (by value or name)."""
    if value is None:
        return None

    s = str(value).strip()
    if not s:
        return None

    try:
        return enum_type(s.lower())
    except Exception:
        pass

    try:
        return enum_type[s.upper()]
    except Exception:
        raise ValueError(f"Invalid enum value '{value}' for {enum_type.__name__}")
