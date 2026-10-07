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
from typing import (
    Any,
    Dict,
    get_origin,
    get_args,
    Optional,
    List,
    Tuple,
    Union,
    Iterable,
)
from enum import Enum

from src.models.entities.model_v31 import *

import logging

DEFAULT_SCHEMA_VERSION = "v31"

# -------- 경로 토크나이저용 정규식 --------
_INDEX_RE = re.compile(r"^\s*(?P<idx>\d+)\s*$")
# tag[@attr='value'] 또는 tag[@attr="value"]
_FILTER_RE = re.compile(
    r"^(?P<tag>[A-Za-z_][\w\-]*)\[@(?P<attr>[\w:.\-]+)=(?P<q>['\"])(?P<val>.*?)(?P=q)\]$"
)

# tag[@attr='value'][3] 또는 tag[@attr="value"][3]  (필터+인덱스 동시)
_COMBO_RE = re.compile(
    r"^(?P<tag>[A-Za-z_][\w\-]*)\[@(?P<attr>[\w:.\-]+)=(?P<q>['\"])(?P<val>.*?)(?P=q)\]\[(?P<idx>\d+)\]$"
)

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


def validate_dtasset_or_raise(xml_text: str) -> None:
    """
    최종 dt_asset XML을 ISO14649 v3(DtAsset) 스키마로 엄격 검증.
    위반 시 ParserError 포함한 ValueError를 던진다.
    """
    try:
        strict_parser.parse(io.BytesIO(xml_text.encode("utf-8")), DtAsset)
    except ParserError as e:
        # xsdata의 ParserError를 그대로 올리면 FastAPI에서 직렬화하기 까다로우니 깔끔하게 래핑
        raise ValueError(f"Schema validation failed: {e}")  # 422로 매핑 예정


def _resolve_enum(enum_type: type[Enum], value) -> Enum:
    """
    CAM JSON 값(value)을 ISO14649 Enum(enum_type)으로 안전하게 변환.
    - 값 매칭(value):   e.g. "climb" -> CutmodeType.CLIMB
    - 이름 매칭(name):   e.g. "CLIMB" -> CutmodeType.CLIMB
    - 대/소문자, 앞뒤 공백 안전
    """
    if value is None:
        return None  # 호출부에서 required 처리

    # 숫자형이 들어오는 경우 문자열화
    if not isinstance(value, str):
        value = str(value)

    s = value.strip()
    if not s:
        return None

    # 1) 값(value) 기반 매칭 (EnumMember.value)
    try:
        return enum_type(s.lower())
    except Exception:
        pass

    # 2) 이름(name) 기반 매칭 (EnumMember.name)
    try:
        return enum_type[s.upper()]
    except Exception:
        raise ValueError(f"잘못된 enum 값 '{value}' for {enum_type.__name__}")


def _coerce_cutmode_or_default(v, default="climb") -> str:
    """Cutmode 전용: 유효하지 않거나 모호한 값은 default로 강제."""
    if v is None:
        return default
    s = str(v).strip().lower()
    if s in ("climb", "conventional"):
        return s
    # 흔히 오는 애매한 값들 → default로 수렴
    if s in ("any", "both", "either", "auto", "neutral", ""):
        return default
    # 알 수 없는 값도 default
    return default


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


## 자식 승격용 내부 함수 - cam json 덮어쓸 때 오류나던 것 처리를 위함 ##
def _snake_name(py_type: type) -> str:
    name = camel_to_snake(getattr(py_type, "__name__", ""))
    return name.replace("two5_d", "two5D", 1) if name.startswith("two5_d") else name


def _class_by_snake(snake_name: str) -> type | None:
    # globals() 에 등록된 dataclass들 중 snake_case 이름이 일치하는 타입을 찾는다
    target = snake_name.strip()
    for _name, obj in globals().items():
        if isinstance(obj, type) and hasattr(obj, "__name__"):
            if camel_to_snake(obj.__name__) == target:
                return obj
    return None


def _inject_or_upgrade_xsi_type(container: Dict[str, Any], key: str, new_type: type):
    """
    container[key] 노드의 @xsi:type 을 설정/업그레이드.
    - 기존 타입이 없으면 new_type으로 설정
    - 기존 타입이 있고, new_type이 기존 타입의 서브클래스면 업그레이드
    - 그 외에는 유지(다운그레이드/무관계 방지)
    """
    node = container.setdefault(key, {})
    if not isinstance(node, dict):
        container[key] = node = {}

    cur = node.get("@xsi:type")
    new_snake = _snake_name(new_type)

    if not cur:
        node["@xsi:type"] = new_snake
        return

    # 현재 타입 -> 파이썬 클래스 역매핑
    cur_cls = _class_by_snake(cur)
    if isinstance(cur_cls, type):
        # 서브클래스면 승격
        if issubclass(new_type, cur_cls):
            node["@xsi:type"] = new_snake
        # 다운그레이드면 무시
        else:
            pass
    else:
        # 현재 타입을 클래스에 매핑 못하면 보수적으로 교체하지 않음
        pass


def create_feature_xml_temp(
    json_data: Dict[str, Any],
    mapping_data: dict,
    dataclass_type=MachiningWorkingstep,  # 루트 스키마 타입
    *,
    strict_required: bool = True,  # ← 추가: 기본은 기존처럼 엄격, 필요 시 False로 완화
) -> str:
    """
    CAM JSON + 매핑(14649 경로) → its_elements XML 생성.

    엄격 모드(strict_required=True):
      - 경로의 '클래스명'은 실제 타입으로 해석. 없으면 에러.
      - 경로의 '필드명'은 current_type의 dataclass 필드에 반드시 존재해야 함. 없으면 에러.
      - required=True 인 필드는 값이 비어 있으면 에러.
      - @xsi:type 은 노드마다 1회만 주입.

    완화 모드(strict_required=False):
      - 상동이나, required 누락을 에러로 올리지 않고 그대로 진행(빈값/누락 허용).
      - 후속 단계(라우터 등)에서 ensure_* 류로 더미 보강 → 최종 전체 XML로 스키마 검증.
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

                # 상위 노드에 xsi:type 1회 주입
                if prev_key is not None and grand_parent is not None:
                    _inject_or_upgrade_xsi_type(grand_parent, prev_key, current_type)

                is_leaf = i == len(path_parts) - 1

                if is_leaf:
                    # CAM 값 추출
                    value = get_nested_value(json_data, json_key.split("."))

                    # --- enum 처리: 값/이름 둘 다 허용 (대소문자 안전)
                    fobj = current_type.__dataclass_fields__[part]
                    enum_type = _resolve_enum_type(fobj.type)
                    if enum_type:
                        # --- CutmodeType만 예외 처리 (기본값 강제) ---
                        if enum_type.__name__ == "CutmodeType":
                            raw = value
                            value = _coerce_cutmode_or_default(value, default="climb")
                            if str(raw).strip().lower() != value:
                                try:
                                    logger.warning(
                                        "Cutmode fallback: %r -> %s", raw, value
                                    )
                                except Exception:
                                    pass
                        else:
                            if value is None or (
                                isinstance(value, str) and not value.strip()
                            ):
                                value = None
                            else:
                                enum_val = _resolve_enum(enum_type, value)
                                value = (
                                    enum_val.value
                                    if isinstance(enum_val, Enum)
                                    else enum_val
                                )

                    # required 즉시 검사(엄격 모드에서만 실패)
                    if fobj.metadata.get("required", False) and strict_required:
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

    # 전체 트리 required 일괄 검사(엄격 모드에서만 예외)
    missing = _validate_required_fields(dataclass_type, nested)
    if missing and strict_required:
        raise ValueError("required 필드 누락: " + ", ".join(missing))
    if missing and not strict_required:
        # 완화 모드: 로그만 남기고 계속 진행
        try:
            logger.warning(
                "[create_feature_xml_temp] required missing (len=%d): %s",
                len(missing),
                ", ".join(missing),
            )
        except Exception:
            pass

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


# -----v3 추가 함수 ----


def _get_by_local(d: dict, local: str):
    """네임스페이스가 있든 없든 로컬명으로 안전 접근."""
    if not isinstance(d, dict):
        return None
    if local in d:
        return d[local]
    for k in d.keys():
        if isinstance(k, str) and (
            k.endswith("}" + local) or k.split(":")[-1] == local
        ):
            return d[k]
    return None


def extract_dtasset_meta(
    xml_string: str, *, strict: bool = True
) -> Dict[str, Optional[str]]:
    """
    dt_asset XML에서 메타데이터 추출.
    반환키: global_asset_id, asset_id, type, category, element_id
    strict=True면 필수 필드 누락 시 ValueError.
    """
    try:
        doc = xmltodict.parse(
            xml_string,
            process_namespaces=True,
            namespaces={
                "http://digital-thread.re/dt_asset": None,
                "http://www.w3.org/2001/XMLSchema-instance": "xsi",
            },
            attr_prefix="@",
        )
    except Exception as e:
        raise ValueError(f"XML 파싱 실패: {e}")

    dt_asset = _get_by_local(doc, "dt_asset")
    if not isinstance(dt_asset, dict):
        raise ValueError("루트에 <dt_asset> 가 없습니다.")

    global_asset_id = _get_by_local(dt_asset, "asset_global_id")
    asset_id = _get_by_local(dt_asset, "id")

    elems = _get_by_local(dt_asset, "dt_elements")
    if elems is None:
        if strict:
            raise ValueError("<dt_asset> 안에 <dt_elements> 가 없습니다.")
        return {
            "global_asset_id": global_asset_id,
            "asset_id": asset_id,
            "type": None,
            "category": None,
            "element_id": None,
        }

    first = elems[0] if isinstance(elems, list) else elems
    if not isinstance(first, dict):
        raise ValueError("<dt_elements> 구조가 올바르지 않습니다.")

    el_type = first.get("@xsi:type") or first.get("xsi:type")
    element_id = _get_by_local(first, "element_id")
    category = _get_by_local(first, "category")

    meta = {
        "global_asset_id": global_asset_id,
        "asset_id": asset_id,
        "type": el_type,
        "category": category,
        "element_id": element_id,
    }

    if strict:
        missing = [
            k
            for k in ("global_asset_id", "asset_id", "type", "element_id")
            if not meta.get(k)
        ]
        if missing:
            raise ValueError(f"필수 메타 누락: {', '.join(missing)}")

    return meta


def ensure_dtasset_namespaces(root: Dict[str, Any]) -> None:
    """루트 dt_asset에 xmlns / xsi 누락 시 보정."""
    if "@xmlns" not in root:
        root["@xmlns"] = "http://digital-thread.re/dt_asset"
    if "@xmlns:xsi" not in root:
        root["@xmlns:xsi"] = "http://www.w3.org/2001/XMLSchema-instance"


def ensure_schema_version(root: Dict[str, Any], schema_version: Optional[str]) -> None:
    """루트에 schemaVersion 속성이 없으면 채움. 주어지면 강제 덮어쓰기."""
    if schema_version:
        root["@schemaVersion"] = schema_version
    else:
        root.setdefault("@schemaVersion", DEFAULT_SCHEMA_VERSION)


# --- 내부 헬퍼: dt_file 노드 선택 ---
def select_dt_file_node(
    root: Dict[str, Any], target_element_id: Optional[str]
) -> Dict[str, Any]:
    """
    dt_asset/dt_elements 중 @xsi:type='dt_file'인 노드를 선택.
    - target_element_id가 주어지면 element_id 매칭
    - 없으면 dt_file이 단 1개일 때만 자동 선택
    """
    dt_asset = root.get("dt_asset") or root
    elems = dt_asset.get("dt_elements")
    if elems is None:
        raise ValueError("dt_asset/dt_elements missing")
    if not isinstance(elems, list):
        elems = [elems]
    files = [
        e for e in elems if isinstance(e, dict) and e.get("@xsi:type") == "dt_file"
    ]
    if not files:
        raise ValueError("No dt_file element")
    if target_element_id:
        for e in files:
            if e.get("element_id") == target_element_id:
                return e
        raise ValueError(f"dt_file element_id='{target_element_id}' not found")
    if len(files) > 1:
        raise ValueError("Multiple dt_file found. Specify target_element_id.")
    return files[0]


def inject_file_id_into_xml(
    *,
    xml: str,
    file_id: str,
    target_element_id: Optional[str],
    fill: str,  # "value" | "path" | "both"
    overwrite: bool,
    default_content_type: str,
    path_template: str,
) -> str:
    d = xmltodict.parse(xml)
    node = select_dt_file_node(d, target_element_id)

    # content_type 없으면 기본값
    if not node.get("content_type"):
        node["content_type"] = default_content_type

    # value/path 주입
    if fill in ("value", "both"):
        if overwrite or not node.get("value"):
            node["value"] = file_id
    if fill in ("path", "both"):
        if overwrite or not node.get("path"):
            node["path"] = path_template.format(oid=file_id)

    return xmltodict.unparse(d)


def infer_type_and_category(type_name: str | None) -> tuple[str | None, str | None]:
    if not type_name:
        return None, None
    t = type_name.lower().strip()

    # 사람 친화 별칭 -> (정식 type, 암시적 category)
    if t in ("nc", "nc_code", "gcode"):
        return "dt_file", "NC"
    if t in ("tdms",):
        return "dt_file", "TDMS"
    if t in ("vm",):
        return "dt_file", "VM"

    if t in ("tool", "cutting_tool", "tool13399", "iso13399"):
        return "dt_cutting_tool_13399", None
    if t in ("machine", "machine_tool"):
        return "dt_machine_tool", None
    if t in ("project",):
        return "dt_project", None

    # 이미 정식 타입이 들어온 경우 (예: dt_file) -> 카테고리는 제한하지 않음
    return type_name, None


# xml  속성 추출 함수
def get_inner_data(project: Union[str, bytes, Dict[str, Any]], path: str) -> str:
    """
    dt_asset XML(문자열/바이트) 또는 이미 파싱된 dict에서 `path`에 해당하는 부분만 XML로 반환.
    - 오류시 HTTP 500을 던지지 않고 <error>...</error> XML을 문자열로 반환.
    - 지원 루트: dt_asset 전용
    - 경로 문법 예:
        "dt_asset/dt_elements[@xsi:type='dt_file'][0]"
        "dt_asset/dt_elements[@xsi:type='dt_project']/main_workplan/its_elements[1]"
        "dt_asset/id"
    """
    try:
        doc = _parse_input(project)
        tokens = _tokenize(path)
        if not tokens:
            return _error_xml("EMPTY_PATH", path, "경로가 비어 있습니다.")

        cur, root_local = _unwrap_root(doc)  # root_local == "dt_asset" 기대
        # 첫 토큰이 루트명이면 스킵 허용
        if tokens and tokens[0]["tag"] == root_local:
            tokens = tokens[1:]

        for step in tokens:
            cur = _apply_step(cur, step)

        # 직렬화
        wrapper = next(
            (t["tag"] for t in reversed(tokens) if t["tag"]), root_local or "result"
        )
        if isinstance(cur, list):
            return _safe_unparse_list(wrapper, cur)
        return xmltodict.unparse({wrapper: cur}, pretty=True, attr_prefix="@")
    except IndexError as e:
        return _error_xml("INDEX_ERROR", path, str(e))
    except KeyError as e:
        return _error_xml("NODE_NOT_FOUND", path, str(e))
    except TypeError as e:
        return _error_xml("TYPE_ERROR", path, str(e))
    except Exception as e:
        return _error_xml("INTERNAL_ERROR", path, f"{type(e).__name__}: {e}")


# -------- 내부 유틸 --------
def _parse_input(project: Union[str, bytes, Dict[str, Any]]) -> Dict[str, Any]:
    if isinstance(project, (str, bytes)):
        # 네임스페이스는 로컬로 풀어 사용 (태그 접근을 단순화)
        return xmltodict.parse(
            project,
            process_namespaces=True,
            namespaces={
                "http://digital-thread.re/dt_asset": None,
                "http://digital-thread.re/iso14649": None,
                "http://www.w3.org/2001/XMLSchema-instance": "xsi",
            },
            attr_prefix="@",  # 속성은 @xxx 로 접근
            cdata_key="#text",  # 텍스트 노드
        )
    if isinstance(project, dict):
        return project
    raise TypeError(f"Unsupported project type: {type(project)}")


def _unwrap_root(doc: Dict[str, Any]) -> Tuple[Dict[str, Any], Optional[str]]:
    """
    최상위 네임스페이스 키를 벗겨 로컬 루트로 진입.
    {'{ns}dt_asset': {...}} -> ({...}, 'dt_asset')
    """
    if isinstance(doc, dict) and len(doc) == 1:
        only_key = next(iter(doc))
        local = only_key.split("}", 1)[-1] if only_key.startswith("{") else only_key
        if local == "dt_asset":
            return doc[only_key], "dt_asset"
    return doc, None


def _tokenize(path: str):
    toks = []
    for raw in filter(None, path.split("/")):
        # 1) 필터+인덱스 동시
        m = _COMBO_RE.match(raw)
        if m:
            toks.append(
                {
                    "tag": m.group("tag"),
                    "index": int(m.group("idx")),
                    "filter": (f"@{m.group('attr')}", m.group("val")),
                }
            )
            continue
        # 2) 필터만
        m = _FILTER_RE.match(raw)
        if m:
            toks.append(
                {
                    "tag": m.group("tag"),
                    "index": None,
                    "filter": (f"@{m.group('attr')}", m.group("val")),
                }
            )
            continue
        # 3) [idx]만
        m = re.match(r"^(?P<tag>[A-Za-z_][\w\-]*)\[(?P<idx>\d+)\]$", raw)
        if m:
            toks.append(
                {
                    "tag": m.group("tag"),
                    "index": int(m.group("idx")),
                    "filter": None,
                }
            )
            continue
        # 4) 폴백 파서: 대괄호가 있는데 위에서 안 걸렸다면 수동 파싱
        if "[" in raw and raw.endswith("]"):
            try:
                tag, cond = raw.split("[", 1)
                cond = cond[:-1]  # trailing ']'
                # cond 형태: @xsi:type='dt_project' or @xsi:type="dt_project"
                m2 = re.match(
                    r"^@(?P<attr>[\w:.\-]+)=(?P<q>['\"])(?P<val>.*?)(?P=q)$", cond
                )
                if m2 and re.match(r"^[A-Za-z_][\w\-]*$", tag):
                    toks.append(
                        {
                            "tag": tag,
                            "index": None,
                            "filter": (f"@{m2.group('attr')}", m2.group("val")),
                        }
                    )
                    continue
            except Exception:
                pass  # 그냥 일반 태그로 떨어지게

        # 5) 순수 숫자 세그먼트 → 인덱스 접근
        if raw.isdigit():
            toks.append({"tag": None, "index": int(raw), "filter": None})
        else:
            toks.append({"tag": raw, "index": None, "filter": None})
    return toks


def _apply_step(cur, step):
    # 인덱스 전용 세그먼트 ( .../3 )
    if step["tag"] is None:
        if not isinstance(cur, list):
            raise KeyError("현재 노드는 리스트가 아닙니다. (인덱스 접근 불가)")
        idx = step["index"]
        if idx < 0 or idx >= len(cur):
            raise IndexError(f"인덱스 범위를 벗어났습니다: {idx}")
        return cur[idx]

    # 자식 찾기
    node = _get_child(cur, step["tag"]) if isinstance(cur, dict) else None
    if node is None:
        raise KeyError(f"태그 없음: {step['tag']}")

    # 리스트면 필터/인덱스 적용, 딕셔너리면 그대로
    if isinstance(node, list):
        # 필터 우선
        if step["filter"]:
            attr_key, expected = step["filter"]
            filtered = [
                e for e in node if isinstance(e, dict) and e.get(attr_key) == expected
            ]
        else:
            filtered = node

        if step["index"] is not None:
            idx = step["index"]
            if idx < 0 or idx >= len(filtered):
                raise IndexError(f"인덱스 범위를 벗어났습니다: {idx}")
            return filtered[idx]
        else:
            return filtered  # 다음 스텝에서 다시 처리
    else:
        # 단일 노드인데 필터가 있으면 즉시 검증
        if step["filter"]:
            attr_key, expected = step["filter"]
            if not (isinstance(node, dict) and node.get(attr_key) == expected):
                raise KeyError(f"필터 불일치: {attr_key}={expected}")
        return node


def _get_child(cur: Dict[str, Any], tag: str) -> Any:
    """
    네임스페이스 제거된 로컬 태그 기준으로 자식 조회.
    xmltodict.parse(..., process_namespaces=True, namespaces={...: None})로
    이미 로컬태그화 되어 있으므로 단순 조회가 대부분 동작.
    """
    if tag in cur:
        return cur[tag]
    # 혹시 다른 네임스페이스 키가 섞여 있으면 로컬명 일치로 스캔
    for k, v in cur.items():
        local = k.split("}", 1)[-1] if isinstance(k, str) and k.startswith("{") else k
        if local == tag:
            return v
    return None


def _safe_unparse_list(elem_name: str, items: List[Any]) -> str:
    """
    루트가 리스트가 되지 않도록 컨테이너를 하나 감싸서 직렬화.
    <elem_name_list><elem_name>...</elem_name>...</elem_name_list>
    """
    container = f"{elem_name}_list"
    return xmltodict.unparse(
        {container: {elem_name: items}}, pretty=True, attr_prefix="@"
    )


def _error_xml(code: str, path: str, detail: str) -> str:
    return xmltodict.unparse(
        {"error": {"code": code, "path": path, "message": detail}},
        pretty=True,
        attr_prefix="@",
    )


# add_ref 관련


def pick_dt_project(root: Dict[str, Any], project_element_id: str) -> Dict[str, Any]:
    dt_asset = root.get("dt_asset") or root
    elems = dt_asset.get("dt_elements")
    if elems is None:
        raise KeyError("dt_asset/dt_elements not found")
    elems = elems if isinstance(elems, list) else [elems]
    for e in elems:
        if (
            isinstance(e, dict)
            and e.get("@xsi:type") == "dt_project"
            and e.get("element_id") == project_element_id
        ):
            return e
    raise KeyError(f"dt_project(element_id='{project_element_id}') not found")


def pick_dt_project_auto(root: Dict[str, Any]) -> Dict[str, Any]:
    """문서에 dt_project가 딱 1개면 그걸 반환, 0개/2개 이상이면 에러."""
    dt_asset = root.get("dt_asset") or root
    elems = dt_asset.get("dt_elements")
    if elems is None:
        raise KeyError("dt_asset/dt_elements not found")
    elems = elems if isinstance(elems, list) else [elems]
    found = [
        e for e in elems if isinstance(e, dict) and e.get("@xsi:type") == "dt_project"
    ]
    if len(found) == 1:
        return found[0]
    if len(found) == 0:
        raise KeyError("no dt_project in asset")
    raise KeyError("multiple dt_project elements in asset; project_element_id required")


def pick_dt_product(root: Dict[str, Any], product_element_id: str) -> Dict[str, Any]:
    dt_asset = root.get("dt_asset") or root
    elems = dt_asset.get("dt_elements")
    if elems is None:
        raise KeyError("dt_asset/dt_elements not found")
    elems = elems if isinstance(elems, list) else [elems]
    for e in elems:
        if (
            isinstance(e, dict)
            and e.get("@xsi:type") == "dt_product"
            and e.get("element_id") == product_element_id
        ):
            return e
    raise KeyError(f"dt_product(element_id='{product_element_id}') not found")


def pick_dt_product_auto(root: Dict[str, Any]) -> Dict[str, Any]:
    """문서에 dt_product가 딱 1개면 그걸 반환, 0개/2개 이상이면 에러."""
    dt_asset = root.get("dt_asset") or root
    elems = dt_asset.get("dt_elements")
    if elems is None:
        raise KeyError("dt_asset/dt_elements not found")
    elems = elems if isinstance(elems, list) else [elems]
    found = [
        e for e in elems if isinstance(e, dict) and e.get("@xsi:type") == "dt_product"
    ]
    if len(found) == 1:
        return found[0]
    if len(found) == 0:
        raise KeyError("no dt_product in asset")
    raise KeyError("multiple dt_product elements in asset; product_element_id required")


def find_elements_in_product(product_node: Dict[str, Any]) -> List[Any]:
    """dt_product의 its_elements를 리스트로 반환(없으면 생성)."""
    if "its_elements" not in product_node:
        product_node["its_elements"] = []
    
    elems = product_node["its_elements"]
    if isinstance(elems, list):
        return elems
    
    # 단일 dict이면 list로 승격
    product_node["its_elements"] = [elems]
    return product_node["its_elements"]


def _as_list(v: Any) -> List[Any]:
    if v is None:
        return []
    return v if isinstance(v, list) else [v]


def _xsi_local(t: str | None) -> str:
    return (t or "").split(":")[-1]


def _iter_nested_workplans(wp_node: Dict[str, Any]):
    """workplan 노드 내부에서 its_elements 중 @xsi:type='workplan'인 하위 워크플랜들을 재귀 순회."""
    for el in _as_list(wp_node.get("its_elements")):
        if not isinstance(el, dict):
            continue
        t = _xsi_local(el.get("@xsi:type") or el.get("xsi:type"))
        if t == "workplan":
            yield el
            # 더 깊은 중첩까지 추적
            yield from _iter_nested_workplans(el)


def find_workplan_in_project(
    project_node: Dict[str, Any], workplan_id: str
) -> Dict[str, Any]:
    """
    - main_workplan 의 its_id 먼저 비교
    - main_workplan 내부 its_elements의 workplan 들을 재귀적으로 찾아 its_id 매칭
    - (프로젝트 레벨 its_elements는 더 이상 보지 않음)
    """
    wp = project_node.get("main_workplan")
    if not isinstance(wp, dict):
        raise KeyError("main_workplan not found in project")

    if (wp.get("its_id") or "").strip() == (workplan_id or "").strip():
        return wp

    for sub in _iter_nested_workplans(wp):
        if (sub.get("its_id") or "").strip() == (workplan_id or "").strip():
            return sub

    raise KeyError("workplan not found in project")


def find_workpiece_in_project(
    project_node: Dict[str, Any], workpiece_id: str
) -> Dict[str, Any]:
    """
    dt_project 아래 workpiece(its_workpieces)를 its_id로 찾아 반환.
    생성하지 않음. 못 찾으면 예외.
    """
    # 일반적으로 반복 태그명이 its_workpieces 로 직렬화됨
    candidates = _as_list(project_node.get("its_workpieces"))
    for c in candidates:
        if not isinstance(c, dict):
            continue
        # ① 직접 구조: <its_workpieces><its_id>...</its_id>...</its_workpieces>
        if c.get("its_id") == workpiece_id:
            return c
        # ② 래핑 구조: <its_workpieces><workpiece>...</workpiece></its_workpieces>
        if "workpiece" in c and isinstance(c["workpiece"], dict):
            w = c["workpiece"]
            if w.get("its_id") == workpiece_id:
                return w

    raise KeyError("workpiece not found in project")


def find_operation_in_workplan(
    workplan_node: Dict[str, Any], workingstep_id: str
) -> Dict[str, Any]:
    """
    workplan 아래 its_elements에서 (…workingstep) 을 its_id로 찾고,
    그 안의 its_operation 노드를 반환.
    - 무접두/접두어 허용
    - machining_workingstep 직접 구조 및 래핑 구조 모두 지원
    """
    for el in _as_list(workplan_node.get("its_elements")):
        if not isinstance(el, dict):
            continue

        # 후보 workingstep 노드 선택
        t = _xsi_local(el.get("@xsi:type") or el.get("xsi:type"))
        if t.endswith("workingstep"):
            ws = el
        elif "workingstep" in el and isinstance(el["workingstep"], dict):
            ws = el["workingstep"]
        else:
            continue

        # its_id 비교 (보호적으로 내부 래핑도 확인)
        ws_id = (
            ws.get("its_id")
            or (ws.get("machining_workingstep", {}) or {}).get("its_id")
            or ""
        ).strip()
        if ws_id != (workingstep_id or "").strip():
            continue

        # its_operation 찾기(직접/내부 래핑 모두)
        op = ws.get("its_operation")
        if isinstance(op, dict):
            return op

        inner = ws.get("machining_workingstep")
        if isinstance(inner, dict):
            op = inner.get("its_operation")
            if isinstance(op, dict):
                return op

    raise KeyError("workingstep not found in workplan")


def build_ref_url(
    *,
    base_uri_prefix: str,
    user_prefix: str,
    ref_global_asset_id: str,
    ref_asset_id: str,
    ref_element_id: str,
) -> str:
    """https://{uri}/{userspecificId}/{globalAssetId}/{AssetId}/{ElementId}"""
    return f"{base_uri_prefix}/{user_prefix}/{ref_global_asset_id}/{ref_asset_id}/{ref_element_id}"


def _normalize_keys_list(ref_obj: Dict[str, Any]) -> List[Dict[str, Any]]:
    """ref_obj['keys'] 를 항상 list[dict] 로 정규화"""
    keys = ref_obj.get("keys")
    if not keys:
        return []
    return keys if isinstance(keys, list) else [keys]


def ref_has_uri(ref_obj: Dict[str, Any], uri: str) -> bool:
    """ref_obj 의 keys[*].value 중 uri 와 동일한 값이 존재하는지 확인"""
    for kv in _normalize_keys_list(ref_obj):
        if kv.get("value") == uri:
            return True
    return False


def _iter_ref_values(parent: Dict[str, Any], tag: str) -> Iterable[str]:
    """
    parent[tag] 에 들어있는 ref 객체들에서 keys[].value 값을 모두 이터레이션.
    - ref 구조 가정: { "keys": [ {"key": "...", "value": "URI"}, ... ] }
    """
    if not isinstance(parent, dict):
        return
    now = parent.get(tag)
    if now is None:
        return

    items = now if isinstance(now, list) else [now]
    for item in items:
        if not isinstance(item, dict):
            continue
        keys = item.get("keys")
        if not isinstance(keys, list):
            continue
        for kv in keys:
            val = kv.get("value")
            if isinstance(val, str):
                yield val


def has_ref_value(parent: Dict[str, Any], tag: str, uri: str) -> bool:
    """이미 동일한 URI가 존재하는지 여부."""
    return any(v == uri for v in _iter_ref_values(parent, tag))


def append_unique_ref(
    parent: Dict[str, Any], tag: str, ref_obj: Dict[str, Any]
) -> bool:
    """
    동일한 URI가 없을 때만 append. 추가되면 True, 이미 있어서 스킵하면 False.
    내부적으로 기존 append_multi_ref 를 재사용.
    """
    # ref_obj에서 첫 value를 뽑아 비교 (관례상 keys[0].value 사용)
    uri = None
    if isinstance(ref_obj, dict):
        keys = ref_obj.get("keys")
        if isinstance(keys, list) and keys:
            uri = keys[0].get("value")

    if isinstance(uri, str) and has_ref_value(parent, tag, uri):
        return False

    # 중복이 아니면 기존 유틸로 추가
    append_multi_ref(parent, tag, ref_obj)
    return True


def _norm_uri(s):
    if s is None:
        return ""
    return str(s).strip().rstrip("/")


def _iter_uri_values_from_keys(keys_node):
    """
    keys_node 가
      - {"key": "...", "value": "..."} 인 dict
      - [{"key": "...", "value": "..."} ...] 인 list
      - None
    어떤 형태든 안전하게 value 값들만 yield
    """
    if not keys_node:
        return
    if isinstance(keys_node, list):
        for kv in keys_node:
            if isinstance(kv, dict) and "value" in kv:
                yield kv["value"]
    elif isinstance(keys_node, dict):
        if "value" in keys_node:
            yield keys_node["value"]


def _iter_uri_values_from_ref_node(ref_node):
    """
    ref_node(dict) 내부의 keys 에 들어있는 모든 value를 yield
    (keys 가 여러 번 반복되거나, 리스트/단일 dict 모두 대응)
    """
    if not isinstance(ref_node, dict):
        return
    keys_field = ref_node.get("keys")
    if keys_field is None:
        return
    # xmltodict 는 동일 태그가 여러 번 나오면 리스트가 되기도 함
    if isinstance(keys_field, list):
        for one in keys_field:
            yield from _iter_uri_values_from_keys(one)
    else:
        # dict 인 경우
        yield from _iter_uri_values_from_keys(keys_field)


def append_multi_ref(parent: dict, tag_name: str, ref_obj: dict) -> None:
    """
    같은 태그 여러 번 나열 지원 + **중복 URI 방지** 추가.
    기존 호출부/시그니처 유지.
    """
    # 이번에 추가하려는 ref_obj 안의 모든 URI 뽑아서 정규화
    new_uris = {_norm_uri(v) for v in _iter_uri_values_from_ref_node(ref_obj)}
    if not new_uris:
        # 비교 기준이 되는 URI가 없으면 그냥 기존 로직대로 append
        existing = parent.get(tag_name)
        if existing is None:
            parent[tag_name] = [ref_obj]
        elif isinstance(existing, list):
            existing.append(ref_obj)
        elif isinstance(existing, dict):
            parent[tag_name] = [existing, ref_obj]
        else:
            parent[tag_name] = [ref_obj]
        return

    def node_has_any_uri(node: dict) -> bool:
        for v in _iter_uri_values_from_ref_node(node):
            if _norm_uri(v) in new_uris:
                return True
        return False

    existing = parent.get(tag_name)

    if existing is None:
        # 처음 추가
        parent[tag_name] = [ref_obj]
        return

    if isinstance(existing, list):
        # 이미 동일 URI가 있으면 추가하지 않음
        for item in existing:
            if isinstance(item, dict) and node_has_any_uri(item):
                return
        existing.append(ref_obj)
        return

    if isinstance(existing, dict):
        # 단일 dict 일 때 동일 URI면 skip, 아니면 list 승격
        if node_has_any_uri(existing):
            return
        parent[tag_name] = [existing, ref_obj]
        return

    # 예외적 타입이면 안전하게 덮어쓰기
    parent[tag_name] = [ref_obj]


def remove_ref_by_uri(parent: Dict[str, Any], tag: str, uri: str) -> bool:
    """
    parent[tag]에 들어있는 ref 객체들 중, keys[].value == uri 인 항목을 삭제.
    - 존재하지 않으면 False (삭제 없음)
    - 삭제하면 True
    - parent[tag]가 dict이면 매칭 시 키 자체를 제거
    - parent[tag]가 list면 해당 아이템만 제거, 모두 사라지면 태그 제거
    """
    now = parent.get(tag)
    if now is None:
        return False

    # 단일(dict)인 경우
    if isinstance(now, dict):
        keys = now.get("keys") or []
        if any(isinstance(k, dict) and k.get("value") == uri for k in keys):
            parent.pop(tag, None)
            return True
        return False

    # 리스트인 경우
    if isinstance(now, list):
        kept: List[Any] = []
        removed = False
        for item in now:
            if isinstance(item, dict):
                keys = item.get("keys") or []
                if any(isinstance(k, dict) and k.get("value") == uri for k in keys):
                    removed = True
                    continue
            kept.append(item)
        if removed:
            if kept:
                parent[tag] = kept
            else:
                parent.pop(tag, None)
            return True
        return False

    # 그 외 형태는 방어적으로 태그 제거 불가
    return False


def split_dt_asset_xml(xml: str) -> List[str]:
    """
    하나의 dt_asset XML을 dt_elements 단위로 쪼개서
    각 결과 XML은 하나의 dt_elements만 포함하도록 만든다.
    루트의 asset_global_id/id/schemaVersion/namespace를 보존한다.
    """
    try:
        doc = xmltodict.parse(
            xml,
            process_namespaces=True,
            namespaces={
                "http://digital-thread.re/dt_asset": None,
                "http://www.w3.org/2001/XMLSchema-instance": "xsi",
            },
            attr_prefix="@",
        )
    except Exception as e:
        raise ValueError(f"XML 파싱 실패: {e}")

    root = _get_by_local(doc, "dt_asset")
    if not root:
        raise ValueError("<dt_asset> not found")

    global_asset_id = _get_by_local(root, "asset_global_id")
    asset_id = _get_by_local(root, "id")
    schema_version = root.get("@schemaVersion") or DEFAULT_SCHEMA_VERSION
    asset_kind = _get_by_local(root, "asset_kind") or "instance"

    elems = _get_by_local(root, "dt_elements")
    if elems is None:
        return []

    items = elems if isinstance(elems, list) else [elems]
    outs: List[str] = []
    for e in items:
        single = {
            "dt_asset": {
                "@xmlns": "http://digital-thread.re/dt_asset",
                "@xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
                "@schemaVersion": schema_version,
                "asset_global_id": global_asset_id,
                "id": asset_id,
                "asset_kind": asset_kind,
                "dt_elements": e,
            }
        }
        outs.append(xmltodict.unparse(single, pretty=True, attr_prefix="@"))
    return outs


def _first_str(val) -> Optional[str]:
    if val is None:
        return None
    if isinstance(val, list):
        for v in val:
            if isinstance(v, str) and v.strip():
                return v.strip()
        return None
    if isinstance(val, str):
        s = val.strip()
        return s or None
    return None


def get_file_display_name(dt_element_node: Dict[str, Any]) -> Optional[str]:
    """dt_file의 표시 파일명 필드 추출 (display_name→file_name→filename 순)."""
    if not isinstance(dt_element_node, dict):
        return None
    return (
        _first_str(_get_by_local(dt_element_node, "display_name"))
        or _first_str(_get_by_local(dt_element_node, "file_name"))
        or _first_str(_get_by_local(dt_element_node, "filename"))
    )


def extract_nc_reference_tuple(
    dt_element_node: Dict[str, Any],
) -> tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
    """
    NC <reference>에서 (DT_PROJECT element_id, WORKPLAN its_id, DT_GLOBAL_ASSET, DT_ASSET) 추출
    - <reference><keys><key>DT_PROJECT</key><value>...</value></keys> ...
    - <reference><keys><key>WORKPLAN</key><value>...</value></keys> ...
    - <reference><keys><key>DT_GLOBAL_ASSET</key><value>...</value></keys> ...
    - <reference><keys><key>DT_ASSET</key><value>...</value></keys> ...
    """
    if not isinstance(dt_element_node, dict):
        return (None, None, None, None)

    ref = _get_by_local(dt_element_node, "reference")
    if not ref:
        return (None, None, None, None)

    keys_list = ref.get("keys")
    keys_list = keys_list if isinstance(keys_list, list) else [keys_list]

    proj = wp = dt_global = dt_asset = None
    for kv in keys_list:
        if not isinstance(kv, dict):
            continue
        k = _get_by_local(kv, "key")
        v = _get_by_local(kv, "value")
        key_up = (k or "").strip().upper()
        val = _first_str(v)
        if key_up == "DT_GLOBAL_ASSET":
            dt_global = val
        elif key_up == "DT_ASSET":
            dt_asset = val
        elif key_up == "DT_PROJECT":
            proj = val
        elif key_up == "WORKPLAN":
            wp = val

    # 상위 키가 없으면 하위 키는 무의미 → 무효화
    if not dt_global or not dt_asset:
        proj, wp = None, None

    return (dt_global, dt_asset, proj, wp)


def project_workplan_exists_in_xml(
    xml_text: str,
    *,
    project_element_id: str,
    workplan_id: str,
) -> bool:
    """
    단일 프로젝트 XML 문자열에서
    - element_id == project_element_id 인 dt_project를 찾고
    - 그 안에서 workplan_id(=its_id)가 main_workplan 또는 하위 workplan에 존재하는지 확인.
    존재하면 True, 없으면 False.
    """
    try:
        # 네임스페이스 로컬화해서 파싱
        doc = xmltodict.parse(
            xml_text,
            process_namespaces=True,
            namespaces={
                "http://digital-thread.re/dt_asset": None,
                "http://digital-thread.re/iso14649": None,
                "http://www.w3.org/2001/XMLSchema-instance": "xsi",
            },
            attr_prefix="@",  # @xsi:type 접근
            cdata_key="#text",
        )

        # 대상 프로젝트 노드 선택
        dt_proj = pick_dt_project(doc, project_element_id)

        # 대상 워크플랜 탐색 (없으면 KeyError)
        _ = find_workplan_in_project(dt_proj, workplan_id)
        return True

    except Exception:
        return False


def project_exists_in_xml(
    xml_text: str,
    *,
    project_element_id: str,
) -> bool:
    """
    단일 프로젝트 XML 문자열에서 element_id == project_element_id 인 dt_project가 존재하면 True.
    """
    try:
        doc = xmltodict.parse(
            xml_text,
            process_namespaces=True,
            namespaces={
                "http://digital-thread.re/dt_asset": None,
                "http://digital-thread.re/iso14649": None,
                "http://www.w3.org/2001/XMLSchema-instance": "xsi",
            },
            attr_prefix="@",
            cdata_key="#text",
        )
        _ = pick_dt_project(doc, project_element_id)
        return True
    except Exception:
        return False


def _pick_project_reference_node(
    dt_element_node: Dict[str, Any],
) -> Dict[str, Any] | None:
    """
    dt_file 내 여러 <reference> 중 '프로젝트를 참조'하는 reference를 선택:
    - keys에 DT_GLOBAL_ASSET, DT_ASSET 가 **모두** 있는 것을 우선 반환
    - 없으면 None
    """
    if not isinstance(dt_element_node, dict):
        return None
    refs = dt_element_node.get("reference")
    for ref in _as_list(refs):
        if not isinstance(ref, dict):
            continue
        keys = ref.get("keys")
        key_entries = _as_list(keys)
        key_names = set()
        for kv in key_entries:
            if isinstance(kv, dict):
                k = kv.get("key")
                if isinstance(k, str):
                    key_names.add(k.strip().upper())
        if "DT_GLOBAL_ASSET" in key_names and "DT_ASSET" in key_names:
            return ref
    return None


def extract_file_reference_tuple(
    dt_element_node: Dict[str, Any],
) -> tuple[Optional[str], Optional[str], Optional[str], Optional[str], Optional[str]]:
    """
    (DT_GLOBAL_ASSET, DT_ASSET, DT_PROJECT, WORKPLAN, WORKINGSTEP) 추출.
    - <reference>가 여러 개인 경우, 프로젝트 참조(reference)를 골라서 파싱
    - keys가 dict/list 어떤 형태든 안전 처리
    """
    if not isinstance(dt_element_node, dict):
        return (None, None, None, None, None)

    ref = _pick_project_reference_node(dt_element_node)
    if not ref:
        # 프로젝트를 참조하는 reference가 없으면 None 반환
        return (None, None, None, None, None)

    keys_list = _as_list(ref.get("keys"))

    proj = wp = ws = dt_global = dt_asset = None
    for kv in keys_list:
        if not isinstance(kv, dict):
            continue
        k = kv.get("key")
        v = kv.get("value")
        key_up = (k or "").strip().upper()
        val = v.strip() if isinstance(v, str) else None
        if key_up == "DT_GLOBAL_ASSET":
            dt_global = val
        elif key_up == "DT_ASSET":
            dt_asset = val
        elif key_up == "DT_PROJECT":
            proj = val
        elif key_up == "WORKPLAN":
            wp = val
        elif key_up == "WORKINGSTEP":
            ws = val

    # 상위 키 없으면 하위 무효화
    if not dt_global or not dt_asset:
        proj = wp = ws = None

    return (dt_global, dt_asset, proj, wp, ws)


def workplan_exists_in_project_xml(
    project_xml: str, project_element_id: str, workplan_id: str
) -> bool:
    try:
        doc = xmltodict.parse(
            project_xml,
            process_namespaces=True,
            namespaces={
                "http://digital-thread.re/dt_asset": None,
                "http://digital-thread.re/iso14649": None,
                "http://www.w3.org/2001/XMLSchema-instance": "xsi",
            },
            attr_prefix="@",
        )
        dt_proj = pick_dt_project(doc, project_element_id)
        _ = find_workplan_in_project(dt_proj, workplan_id)
        return True
    except Exception:
        return False


def workingstep_exists_in_project_xml(
    project_xml: str, project_element_id: str, workplan_id: str, workingstep_id: str
) -> bool:
    try:
        doc = xmltodict.parse(
            project_xml,
            process_namespaces=True,
            namespaces={
                "http://digital-thread.re/dt_asset": None,
                "http://digital-thread.re/iso14649": None,
                "http://www.w3.org/2001/XMLSchema-instance": "xsi",
            },
            attr_prefix="@",
        )
        dt_proj = pick_dt_project(doc, project_element_id)
        wp = find_workplan_in_project(dt_proj, workplan_id)

        for el in _as_list(wp.get("its_elements")):
            if not isinstance(el, dict):
                continue

            # 1) 타입 기반 매칭 (무접두/접두어 모두 허용)
            t = _xsi_local(el.get("@xsi:type") or el.get("xsi:type"))
            if t.endswith("workingstep"):
                ws = el
            # 2) 래핑 구조 {"workingstep": {...}}
            elif "workingstep" in el and isinstance(el["workingstep"], dict):
                ws = el["workingstep"]
            else:
                continue

            # its_id 비교 (보호적으로 내부 래핑도 확인)
            ws_id = (
                ws.get("its_id")
                or (ws.get("machining_workingstep", {}) or {}).get("its_id")
                or ""
            ).strip()
            if ws_id == (workingstep_id or "").strip():
                return True

        return False
    except Exception:
        return False


def __looks_like_objectid(s: str) -> bool:
    if not isinstance(s, str):
        return False
    return bool(re.fullmatch(r"[0-9a-fA-F]{24}", s.strip()))


def __first_oid_from_dtfile_node(node: Dict[str, Any]) -> Optional[str]:
    """
    dt_file 노드(dict)에서 파일 OID로 보이는 값을 하나 찾아 반환.
    우선순위:
      1) <value> 텍스트
      2) <keys> 안의 (key가 *_id 이거나 value가 OID로 보이는 경우)의 value
    """
    if not isinstance(node, dict):
        return None

    # 1) <value>
    val = node.get("value")
    if isinstance(val, str) and __looks_like_objectid(val):
        return val

    # 2) <keys> (단일/리스트 모두 지원)
    keys = node.get("keys")
    key_items = (
        keys if isinstance(keys, list) else ([keys] if isinstance(keys, dict) else [])
    )
    for kv in key_items:
        if not isinstance(kv, dict):
            continue
        k = _get_by_local(kv, "key")
        v = _get_by_local(kv, "value")
        if isinstance(v, str) and __looks_like_objectid(v):
            # 키가 *_id 이거나, 그 외라도 value가 OID면 채택
            if isinstance(k, str):
                if k.endswith("_id") or k.lower() in ("file_id", "oid", "gridfs_id"):
                    return v
            else:
                return v
    return None


def extract_dtfile_oid(
    xml_text: str, target_element_id: Optional[str] = None
) -> Optional[str]:
    """
    dt_asset XML 문자열에서 대상 dt_file(element_id 지정 가능)로부터 파일 OID를 추출.
    - target_element_id가 None이면 문서 내 dt_file이 1개일 때만 자동 선택.
    - 찾지 못하면 None 반환.
    """
    try:
        doc = xmltodict.parse(
            xml_text,
            process_namespaces=True,
            namespaces={
                "http://digital-thread.re/dt_asset": None,
                "http://www.w3.org/2001/XMLSchema-instance": "xsi",
            },
            attr_prefix="@",
        )
        dt_asset = _get_by_local(doc, "dt_asset")
        if not isinstance(dt_asset, dict):
            return None

        elems = _get_by_local(dt_asset, "dt_elements")
        if elems is None:
            return None
        elems = elems if isinstance(elems, list) else [elems]

        # dt_file 후보 수집
        files = [
            e
            for e in elems
            if isinstance(e, dict)
            and (e.get("@xsi:type") == "dt_file" or e.get("xsi:type") == "dt_file")
        ]
        if not files:
            return None

        target = None
        if target_element_id:
            for e in files:
                if _get_by_local(e, "element_id") == target_element_id:
                    target = e
                    break
            if target is None:
                return None
        else:
            if len(files) != 1:
                # 모호하면 None
                return None
            target = files[0]

        return __first_oid_from_dtfile_node(target)
    except Exception:
        return None


## -- 새로 추가된 Cam json 파싱 관련 유틸 -- ##
def _move_keys_to_tail(d: Dict[str, Any], keys: Iterable[str]) -> None:
    """지정한 키들을 dict의 끝으로 이동(pop → 재할당)."""
    for k in keys:
        if isinstance(d, dict) and k in d:
            d[k] = d.pop(k)


def _push_ref_tags_to_end_in_workplan(wp: Dict[str, Any]) -> None:
    """
    workplan 딕셔너리에서 ref_* 키들을 항상 맨 뒤로 이동.
    중첩된 하위 workplan에도 재귀 적용.
    """
    if not isinstance(wp, dict):
        return

    # 현재 워크플랜에서 ref_* 키를 맨 뒤로
    ref_keys = [
        k for k in list(wp.keys()) if isinstance(k, str) and k.startswith("ref_")
    ]
    _move_keys_to_tail(wp, ref_keys)

    # 하위 workplan들도 정리
    for el in _as_list(wp.get("its_elements")):
        if not isinstance(el, dict):
            continue
        t = _xsi_local(el.get("@xsi:type") or el.get("xsi:type"))
        if t == "workplan":
            _push_ref_tags_to_end_in_workplan(el)


def append_ws_into_project_xml(
    *,
    project_xml_text: str,
    project_element_id: str,
    workplan_id: str,
    ws_node_dict: Dict[str, Any],
) -> str:
    """
    dt_project XML에 workingstep(its_elements 한 덩어리)을 해당 workplan 아래 its_elements로 append.
    반환: 갱신된 전체 프로젝트 dt_asset XML 문자열
    """
    doc = xmltodict.parse(
        project_xml_text,
        process_namespaces=True,
        namespaces={
            "http://digital-thread.re/dt_asset": None,
            "http://digital-thread.re/iso14649": None,
            "http://www.w3.org/2001/XMLSchema-instance": "xsi",
        },
        attr_prefix="@",
    )
    dt_asset = doc.get("dt_asset") or doc
    proj = pick_dt_project(dt_asset, project_element_id)
    wp = find_workplan_in_project(proj, workplan_id)

    # its_elements 추가
    cur = wp.get("its_elements")
    if cur is None:
        wp["its_elements"] = [ws_node_dict]
    elif isinstance(cur, list):
        cur.append(ws_node_dict)
    else:
        wp["its_elements"] = [cur, ws_node_dict]

    # ref_*를 항상 맨 뒤로 재정렬
    _push_ref_tags_to_end_in_workplan(wp)

    ensure_dtasset_namespaces(dt_asset)  # 안전 보정
    return xmltodict.unparse({"dt_asset": dt_asset}, pretty=True, attr_prefix="@")


def inject_cutting_tool_ref(
    ws_node_dict: Dict[str, Any],
    *,
    tool_uri: str,  # 예: https://.../{asset}/{tool_elem}
    dt_global_url: str,  # (이제는 사용하지 않음, 호환 위해 파라미터만 유지)
    tool_asset_id: str,  # (이제는 사용하지 않음, 호환 위해 파라미터만 유지)
    tool_element_id: str,  # ref_dt_cutting_tool.element_id 에 동일 값 사용
    display_name: str = "Cutting Tool Ref",
) -> None:
    """
    workingstep dict 의 its_operation → MachiningOperation 에
    ref_dt_cutting_tool(DtElement 상속)을 다음 형태로 주입:

      <ref_dt_cutting_tool>
        <element_id>{tool_element_id}</element_id>
        <category>reference</category>
        <display_name>{display_name}</display_name>
        <keys>
          <key>DT_ELEMENT_FULLPATH</key>
          <value>{tool_uri}</value>
        </keys>
      </ref_dt_cutting_tool>

    ※ 기존에 여러 keys(URI/DT_GLOBAL_ASSET/DT_ASSET/DT_ELEMENT) 넣던 방식을 폐기.
    """
    if not isinstance(ws_node_dict, dict):
        return

    op = ws_node_dict.get("its_operation")
    if not isinstance(op, dict):
        return

    # MachiningOperation 노드 찾기 (케이스/래핑 다양성 방지)
    mo = op.get("MachiningOperation") or op.get("machining_operation") or op
    if not isinstance(mo, dict):
        return

    # 요청: its_tool은 더미만 유지 가능(혹은 제거). 지금은 더미 유지 정책이면 건드리지 않아도 됨.
    # mo.pop("its_tool", None)  # 더미를 유지하려면 이 줄은 주석 유지

    # 원하는 형태로 ref 구성
    mo["ref_dt_cutting_tool"] = {
        "element_id": tool_element_id,
        "category": "reference",
        "display_name": display_name,
        "keys": {
            "key": "DT_ELEMENT_FULLPATH",
            "value": tool_uri,
        },
    }


def count_workingsteps_in_workplan_xml(
    project_xml: str, project_element_id: str, workplan_id: str
) -> int:
    doc = xmltodict.parse(
        project_xml,
        process_namespaces=True,
        namespaces={
            "http://digital-thread.re/dt_asset": None,
            "http://digital-thread.re/iso14649": None,
            "http://www.w3.org/2001/XMLSchema-instance": "xsi",
        },
        attr_prefix="@",
    )
    dt_proj = pick_dt_project(doc, project_element_id)
    wp = find_workplan_in_project(dt_proj, workplan_id)

    cnt = 0
    for el in _as_list(wp.get("its_elements")):
        if not isinstance(el, dict):  # ⚠️ typing.Dict 말고 내장 dict 사용
            continue

        # 무접두/접두어 안전한 타입 판별
        t = _xsi_local(el.get("@xsi:type") or el.get("xsi:type"))

        # 1) @xsi:type 이 '...workingstep'로 끝나면 카운트 (예: workingstep, machining_workingstep)
        if t and t.endswith("workingstep"):
            cnt += 1
            continue

        # 2) 래핑 구조: {"workingstep": {...}} 혹은 {"machining_workingstep": {...}}
        if isinstance(el.get("workingstep"), dict) or isinstance(
            el.get("machining_workingstep"), dict
        ):
            cnt += 1
            continue

    return cnt


def generate_nc_ids(project_asset_id: str, workplan_id: str) -> tuple[str, str]:
    """
    프로젝트 asset_id, workplan_id 를 기반으로
    - NC dt_asset 의 id
    - NC dt_file 의 element_id
    를 자동 생성한다.
    예:
      project_asset_id = "prj_011" → nc_asset_id = "nc_prj_011"
      workplan_id      = "wp_001"  → nc_element_id = "nc_wp_001"
    """

    def _sanitize(s: str) -> str:
        # 공백/양끝 제거 + XML id에 애매한 문자들은 '_' 로 치환
        s = (s or "").strip()
        return re.sub(r"[^\w\-]+", "_", s)

    proj_id_clean = _sanitize(project_asset_id)
    wp_id_clean = _sanitize(workplan_id)

    nc_asset_id = f"nc_{proj_id_clean}"
    nc_element_id = f"nc_{wp_id_clean}"

    return nc_asset_id, nc_element_id


def build_nc_dt_file_xml(
    *,
    # 새로 만들 NC dt_asset 쪽 메타
    nc_global_asset_id: str,  # 프로젝트와 동일
    project_asset_id: str,  # prj_011
    project_element_id: str,  # milling_prj
    workplan_id: str,  # wp_001
    file_oid: str,  # GridFS OID (24 hex)
    file_name: str,  # display_name 에 들어갈 실제 파일명
) -> str:
    """
    신규 NC dt_file dt_asset XML을 생성한다.
    - asset_global_id: 프로젝트와 동일
    - id / element_id: generate_nc_ids 규칙 사용
    - reference: DT_GLOBAL_ASSET / DT_ASSET / DT_PROJECT / WORKPLAN 채움
    - value: GridFS OID
    """
    nc_asset_id, nc_element_id = generate_nc_ids(project_asset_id, workplan_id)

    # dt_asset 루트 dict (ensure_* 유틸로 네임스페이스/버전 보정)
    dt_asset_root = {
        "asset_global_id": nc_global_asset_id,
        "id": nc_asset_id,
        "asset_kind": "instance",
        "dt_elements": {
            "@xsi:type": "dt_file",
            "element_id": nc_element_id,
            "category": "NC",
            "display_name": file_name,
            "element_description": "NC program file.",
            "content_type": "text/x-gcode",
            "value": file_oid,
            "path": "",
            "reference": {
                # 예시 XML에서도 element_id 는 비워져 있어서 그대로 빈값 유지
                "element_id": "",
                "keys": [
                    {
                        "key": "DT_GLOBAL_ASSET",
                        "value": nc_global_asset_id,
                    },
                    {
                        "key": "DT_ASSET",
                        "value": project_asset_id,
                    },
                    {
                        "key": "DT_PROJECT",
                        "value": project_element_id,
                    },
                    {
                        "key": "WORKPLAN",
                        "value": workplan_id,
                    },
                ],
            },
        },
    }

    # 네임스페이스 / schemaVersion 보정 (이 파일에 이미 있는 유틸 재사용)
    ensure_dtasset_namespaces(dt_asset_root)
    ensure_schema_version(dt_asset_root, None)

    xml = xmltodict.unparse({"dt_asset": dt_asset_root}, pretty=True, attr_prefix="@")

    # xsdata DtAsset 스키마로 최종 검증
    validate_dtasset_or_raise(xml)

    return xml


def generate_step_thumbnail_ids(project_asset_id: str) -> tuple[str, str]:
    """
    프로젝트 asset_id 기반으로 썸네일 dt_file의 (asset_id, element_id)를 고정 생성.
    -> API를 여러 번 호출해도 동일 키로 upsert/update 가능(idempotent)
    """

    def _sanitize(s: str) -> str:
        s = (s or "").strip()
        return re.sub(r"[^\w\-]+", "_", s)

    proj = _sanitize(project_asset_id)

    image_asset_id = f"img_{proj}"
    image_element_id = f"img_{proj}_step_thumb"
    return image_asset_id, image_element_id


def build_step_thumbnail_image_dt_file_xml(
    *,
    project_global_asset_id: str,  # ✅ 프로젝트 global_asset_id를 그대로 사용
    project_asset_id: str,
    project_element_id: str,
    file_oid: str,
    file_name: str,
) -> str:
    """
    STEP 썸네일(PNG)용 TITLE_IMAGE dt_file dt_asset XML 생성
    - 프로젝트 대표 이미지 성격이므로 WORKPLAN reference는 포함하지 않음
    """
    image_asset_id, image_element_id = generate_step_thumbnail_ids(project_asset_id)

    dt_asset_root = {
        "asset_global_id": project_global_asset_id,
        "id": image_asset_id,
        "asset_kind": "instance",
        "dt_elements": {
            "@xsi:type": "dt_file",
            "element_id": image_element_id,
            "category": "TITLE_IMAGE",  # ✅ 변경
            "display_name": file_name,
            "element_description": "STEP thumbnail image (png).",
            "content_type": "image/png",
            "value": file_oid,
            "path": "",
            "reference": {
                "element_id": "",
                "keys": [
                    {"key": "DT_GLOBAL_ASSET", "value": project_global_asset_id},
                    {"key": "DT_ASSET", "value": project_asset_id},
                    {"key": "DT_PROJECT", "value": project_element_id},
                    # ✅ WORKPLAN 제거
                ],
            },
        },
    }

    ensure_dtasset_namespaces(dt_asset_root)
    ensure_schema_version(dt_asset_root, None)

    xml = xmltodict.unparse({"dt_asset": dt_asset_root}, pretty=True, attr_prefix="@")
    validate_dtasset_or_raise(xml)
    return xml
