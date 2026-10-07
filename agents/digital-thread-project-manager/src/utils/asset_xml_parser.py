import re, io
import xmltodict
import dataclasses
from xsdata.formats.dataclass.parsers import XmlParser
from xsdata.formats.dataclass.parsers.config import ParserConfig
from xsdata.formats.dataclass.context import XmlContext
from xsdata.utils import text
from xsdata.formats.dataclass.context import XmlContext
from xsdata.formats.dataclass.serializers import XmlSerializer
from xsdata.formats.dataclass.serializers.config import SerializerConfig
from xsdata.exceptions import ParserError
import xml.etree.ElementTree as ET
from typing import Any, Dict, get_origin, get_args, Optional
from enum import Enum
from src.models.entities.model_v27 import *

import logging

logger = logging.getLogger(__name__)
if not logger.handlers:  # 중복 핸들러 방지
    logging.basicConfig(
        level=logging.INFO,  # 필요시 DEBUG
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )

# --- xsdata 파서 및 시리얼라이저 설정 ---

# 관대한 파서 (스키마에 없는 속성은 무시)
lenient_parser_config = ParserConfig(fail_on_unknown_properties=False)
lenient_context = XmlContext(element_name_generator=text.snake_case)
lenient_parser = XmlParser(config=lenient_parser_config, context=lenient_context)

# 엄격한 파서 (유효성 검증용)
strict_parser = XmlParser()

# XML 생성용 시리얼라이저
serializer_config = SerializerConfig(pretty_print=True)
serializer = XmlSerializer(config=serializer_config)


def validate_xml_against_schema(xml_content: str) -> bool:
    """
    주어진 XML 문자열이 DtAsset 스키마 구조에 맞는지 엄격하게 검증합니다.
    """
    try:
        # 문자열을 바이트로 변환하여 BytesIO 사용
        xml_bytes = xml_content.encode("utf-8")
        stream = io.BytesIO(xml_bytes)

        # 엄격한 파서(strict_parser)를 사용하여 검증
        strict_parser.parse(stream, DtAsset)
        logger.info("성공: XML이 스키마 구조와 일치합니다.")
        return True
    except ParserError as e:
        logger.error("실패: XML이 스키마 구조와 일치하지 않습니다. 오류 원인: %s", e)
        return False


def to_camel_case(snake_str):
    components = snake_str.split("_")
    return "".join(x.title() for x in components)


def ensure_empty_lists(data):
    """빈 리스트([])를 XML 변환 시 빈 태그(<tag></tag>)로 유지"""
    if isinstance(data, dict):
        return {k: ensure_empty_lists(v) if v != [] else "" for k, v in data.items()}
    elif isinstance(data, list):
        return "" if not data else [ensure_empty_lists(v) for v in data]
    return data


def remove_empty_lists(data):
    """리스트가 [None]인 경우, None으로 변환"""
    if isinstance(data, dict):
        return {k: remove_empty_lists(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [] if data == [None] else [remove_empty_lists(v) for v in data]
    return data


def get_class_by_name(class_name):
    return globals().get(class_name)


def camel_to_snake(name):
    """camelCase 문자열을 snake_case로 변환하는 함수"""
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


def convert_type_to_xsi_type(elem):
    # 자식 요소 중에 <type> 태그가 있으면 xsi:type으로 변환
    for child in list(elem):
        if child.tag == "type":
            # 부모 요소에 xsi:type 속성 추가
            elem.set(
                "{http://www.w3.org/2001/XMLSchema-instance}type",
                camel_to_snake(child.text),
            )
            # <type> 태그 삭제
            elem.remove(child)
        # 재귀적으로 자식 요소들도 검사
        convert_type_to_xsi_type(child)


def add_namespace_and_type(xml_str):
    # 'xmlns:xsi'와 'xsi:type' 속성 추가 (its_elements와 project)
    xml_str = xml_str.replace(
        "<its_elements>",
        '<its_elements xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:type="machining_workingstep">',
    )
    xml_str = xml_str.replace(
        "<project>", '<project xmlns="http://www.digital-thread.re/iso14649">'
    )
    return xml_str


def dict_to_xml(parent, data):
    for key, value in data.items():
        attributes = {}
        if isinstance(value, dict):
            keys_to_remove = []
            for attr_key in value.keys():
                if attr_key.startswith("@"):
                    attr_name = attr_key[1:]
                    attributes[attr_name] = value[attr_key]
                    keys_to_remove.append(attr_key)
            for attr_key in keys_to_remove:
                del value[attr_key]

        if isinstance(value, list):
            for item in value:
                dict_to_xml(parent, {key: item})
            continue

        if isinstance(value, dict):
            child = ET.SubElement(parent, key, attributes)
            dict_to_xml(child, value)
        else:
            child = ET.SubElement(parent, key, attributes)
            child.text = str(value) if value is not None else ""


def _resolve_enum_type(field_type) -> Optional[type]:
    """Optional/Union 안에 Enum 타입이 들어있어도 꺼내줌."""
    try:
        origin = get_origin(field_type)
        if origin is not None:
            for a in get_args(field_type):
                if isinstance(a, type) and issubclass(a, Enum):
                    return a
            return None
        return (
            field_type
            if (isinstance(field_type, type) and issubclass(field_type, Enum))
            else None
        )
    except Exception:
        return None


def _resolve_dataclass_field_type(field_type) -> Optional[type]:
    """Optional/Union[List[T]] 처럼 감싸진 dataclass 타입을 되도록 꺼내줌(대략적)."""
    origin = get_origin(field_type)
    if origin is None:
        return field_type if hasattr(field_type, "__dataclass_fields__") else None
    args = [a for a in get_args(field_type) if isinstance(a, type)]
    for a in args:
        if hasattr(a, "__dataclass_fields__"):
            return a
    return None


def _inject_xsi_type_once(container: Dict[str, Any], key: str, py_type: type):
    """같은 노드에 @xsi:type을 한 번만 설정."""
    if not isinstance(container.get(key), dict):
        container[key] = {}
    if "@xsi:type" not in container[key]:
        name = camel_to_snake(getattr(py_type, "__name__", ""))
        if name.startswith("two5_d"):
            name = name.replace("two5_d", "two5D", 1)
        if name:
            container[key]["@xsi:type"] = name


def _validate_required_fields(
    dataclass_type: type, node: Dict[str, Any], path: str = ""
) -> list[str]:
    """
    dataclass_type의 필드 중 metadata['required']==True 인 필드가
    node에 누락/빈 값인지 재귀적으로 검사하고, 누락 경로를 리스트로 반환.
    """
    missing = []
    if not hasattr(dataclass_type, "__dataclass_fields__"):
        return missing

    for fname, fobj in dataclass_type.__dataclass_fields__.items():
        fmeta = getattr(fobj, "metadata", {}) or {}
        fpath = f"{path}.{fname}" if path else fname

        present = fname in node
        val = node.get(fname)

        # required 검사
        if fmeta.get("required", False):
            if (
                (not present)
                or val in (None, "", {})
                or (isinstance(val, list) and len(val) == 0)
            ):
                missing.append(fpath)

        # 하위 dataclass 검사
        inner_dt = _resolve_dataclass_field_type(fobj.type)
        if inner_dt and isinstance(val, dict):
            missing.extend(_validate_required_fields(inner_dt, val, fpath))
        elif inner_dt and isinstance(val, list):
            # 리스트일 경우 각 아이템에 대해 검사(가능하면)
            for i, it in enumerate(val):
                if isinstance(it, dict):
                    missing.extend(
                        _validate_required_fields(inner_dt, it, f"{fpath}[{i}]")
                    )
    return missing


def create_feature_xml(
    json_data: Dict[str, Any], mapping_data: dict, dataclass_type=MachiningWorkingstep
):
    nested_structure = {
        "its_id": {},
        "its_secplane": {},
        "its_feature": {},
        "its_operation": {},
        "its_effect": {},
    }

    # 노드별로 가장 구체적인 파이썬 타입을 기억하는 사이드카
    node_type_map: dict[int, type] = {}

    for json_key, dataclass_path in mapping_data.items():
        path_parts = dataclass_path.split(".")
        current_type = dataclass_type
        parent = nested_structure
        grand_parent = None
        prev_key = None

        for i, part in enumerate(path_parts):
            if part[0].isupper():
                # 클래스 전환(기존 로직 그대로)
                if part in globals():
                    new_type = globals()[part]
                    if isinstance(new_type, type):
                        if prev_key and prev_key[0].isupper():
                            parent_type = globals().get(prev_key)
                            if (
                                parent_type
                                and isinstance(parent_type, type)
                                and issubclass(new_type, parent_type)
                            ):
                                current_type = new_type
                        else:
                            current_type = new_type
            else:
                # 필요한 중간 노드 생성(기존 로직)
                if (
                    hasattr(current_type, "__dataclass_fields__")
                    and part in current_type.__dataclass_fields__
                ):
                    if part not in parent:
                        parent[part] = {}

                # ---- 여기만 변경: xsi:type 승격만 허용 ----
                if prev_key is not None and grand_parent is not None:
                    node = grand_parent.setdefault(prev_key, {})
                    cur_t = node_type_map.get(id(node))
                    # cur_t가 없거나, 새 타입이 더 구체적이면 업그레이드
                    if (cur_t is None) or issubclass(current_type, cur_t):
                        node_type_map[id(node)] = current_type
                        name = camel_to_snake(current_type.__name__)
                        if name.startswith("two5_d"):
                            name = name.replace("two5_d", "two5D", 1)
                        node["@xsi:type"] = name
                    # 그렇지 않으면(다운그레이드) 무시

                # 리프 값 주입(기존 로직)
                if i == len(path_parts) - 1:
                    value = get_nested_value(json_data, json_key.split("."))

                    if (
                        hasattr(current_type, "__dataclass_fields__")
                        and part in current_type.__dataclass_fields__
                    ):
                        field_type = current_type.__dataclass_fields__[part].type
                        if isinstance(field_type, type) and issubclass(
                            field_type, Enum
                        ):
                            if isinstance(value, str):
                                try:
                                    value = field_type[value]
                                except KeyError:
                                    raise ValueError(
                                        f"Invalid value '{value}' for enum {field_type.__name__}"
                                    )
                    parent[part] = value

                grand_parent = parent
                prev_key = part
                parent = parent[part]

    root = ET.Element(
        "its_elements",
        {
            "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
            "xsi:type": "machining_workingstep",
        },
    )
    dict_to_xml(root, nested_structure)
    return ET.tostring(root, encoding="unicode", method="xml")


def create_feature_xml_temp(
    json_data: Dict[str, Any],
    mapping_data: dict,
    dataclass_type=MachiningWorkingstep,  # 루트 스키마 타입
) -> str:
    """
    엄격 모드:
    - 경로의 '클래스명'은 실제 타입으로 해석. 없으면 에러.
    - 경로의 '필드명'은 current_type의 dataclass 필드에 반드시 존재해야 함. 없으면 에러.
    - required=True 인 필드는 값이 비어 있으면 에러.
    - @xsi:type 은 노드마다 1회만 주입.
    """
    nested = {
        "its_id": {},
        "its_secplane": {},
        "its_feature": {},
        "its_operation": {},
        "its_effect": {},
    }

    for json_key, dataclass_path in mapping_data.items():
        path_parts = dataclass_path.split(".")
        current_type = dataclass_type
        parent = nested
        grand_parent = None
        prev_key = None

        for i, part in enumerate(path_parts):
            if not part:
                raise ValueError(
                    f"빈 path 토큰: '{dataclass_path}' (json_key={json_key})"
                )

            if part[0].isupper():
                # ---- 클래스명 전환(엄격) ----
                new_type = globals().get(part)
                if not (isinstance(new_type, type)):
                    raise ValueError(
                        f"알 수 없는 클래스명 '{part}' in path '{dataclass_path}' (json_key={json_key})"
                    )
                current_type = new_type
            else:
                # ---- 필드명(엄격: 타입에 실제 필드가 있어야 함) ----
                if (
                    not hasattr(current_type, "__dataclass_fields__")
                    or part not in current_type.__dataclass_fields__
                ):
                    raise ValueError(
                        f"스키마 불일치: '{getattr(current_type,'__name__',current_type)}'에 필드 '{part}' 없음 "
                        f"(json_key={json_key}, path={dataclass_path})"
                    )

                # grand_parent에 xsi:type 1회 주입
                if prev_key is not None and grand_parent is not None:
                    _inject_xsi_type_once(grand_parent, prev_key, current_type)

                is_leaf = i == len(path_parts) - 1

                if is_leaf:
                    # 값 가져오기
                    value = get_nested_value(json_data, json_key.split("."))

                    # enum 처리
                    fobj = current_type.__dataclass_fields__[part]
                    enum_type = _resolve_enum_type(fobj.type)
                    if enum_type and isinstance(value, str):
                        try:
                            value = enum_type[value]
                        except KeyError:
                            raise ValueError(
                                f"잘못된 enum 값 '{value}' for {enum_type.__name__} "
                                f"(json_key={json_key}, path={dataclass_path})"
                            )

                    # required 필드 즉시 검사
                    if fobj.metadata.get("required", False):
                        if value in (None, ""):
                            raise ValueError(
                                f"required 필드 누락: '{part}' "
                                f"(json_key={json_key}, path={dataclass_path})"
                            )

                    parent[part] = value
                else:
                    # 중간 노드: dict 보장
                    if part not in parent or not isinstance(parent[part], dict):
                        parent[part] = {}
                    # 하강
                    grand_parent = parent
                    prev_key = part
                    parent = parent[part]

    # 전체 트리 required 일괄 검사(누락 모아 보고)
    missing = _validate_required_fields(dataclass_type, nested)
    if missing:
        raise ValueError("required 필드 누락: " + ", ".join(missing))

    # XML 생성
    root = ET.Element(
        "its_elements",
        {
            "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
            "xsi:type": "machining_workingstep",
        },
    )
    dict_to_xml(root, nested)
    return ET.tostring(root, encoding="unicode", method="xml")


def get_nested_value(data: Dict[str, Any], keys: list):
    for key in keys:
        if isinstance(data, dict) and key in data:
            data = data[key]
        else:
            return None
    return data


def dataclass_to_dict(data) -> Dict:
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


def merge_dicts(original: Dict, updates: Dict) -> Dict:
    merged = {}
    all_keys = set(original.keys()).union(set(updates.keys()))

    for key in all_keys:
        original_value = original.get(key)
        update_value = updates.get(key)

        # "@"로 시작하는 속성 키는 한쪽에 없어도 유지
        if key.startswith("@"):
            merged[key] = original_value if original_value is not None else update_value
            continue

        # 한쪽이 None이면 다른 쪽 값을 유지
        if original_value is None:
            merged[key] = update_value
            continue
        if update_value is None:
            merged[key] = original_value
            continue

        # 둘 다 딕셔너리면 재귀적으로 병합
        if isinstance(original_value, dict) and isinstance(update_value, dict):
            merged[key] = merge_dicts(original_value, update_value)
            continue

        # XML에서는 단일 값(`{}`)으로 저장되었지만, dataclass에서는 리스트(`[]`)인 경우
        if isinstance(original_value, dict) and isinstance(update_value, list):
            merged[key] = (
                [merge_dicts(original_value, update_value[0])]
                if update_value
                else [original_value]
            )
            continue
        if isinstance(original_value, list) and isinstance(update_value, dict):
            merged[key] = (
                [merge_dicts(update_value, original_value[0])]
                if original_value
                else [update_value]
            )
            continue

        # 리스트끼리 병합
        if isinstance(original_value, list) and isinstance(update_value, list):
            merged[key] = [
                merge_dicts(o, u) if isinstance(o, dict) and isinstance(u, dict) else u
                for o, u in zip(original_value, update_value)
            ]
            continue

        merged[key] = update_value

    return merged
