import re
import xmltodict
import dataclasses
from xsdata.formats.dataclass.parsers import XmlParser
from xsdata.formats.dataclass.parsers.config import ParserConfig
from xsdata.formats.dataclass.context import XmlContext
from xsdata.utils import text
from xsdata.formats.dataclass.context import XmlContext
from xsdata.formats.dataclass.serializers import XmlSerializer
from xsdata.formats.dataclass.serializers.config import SerializerConfig
import xml.etree.ElementTree as ET
from typing import Any, Dict
from src.models.entities.model import *

parser_config = ParserConfig(fail_on_unknown_properties=False)
context = XmlContext(element_name_generator=text.snake_case)
parser = XmlParser(config=parser_config, context=context)


config = SerializerConfig(indent="    ")
context = XmlContext(element_name_generator=text.snake_case)
serializer = XmlSerializer(context=context, config=config)

def to_camel_case(snake_str):
    components = snake_str.split('_')  
    return ''.join(x.title() for x in components)  

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
    return re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()

def convert_type_to_xsi_type(elem):
    # 자식 요소 중에 <type> 태그가 있으면 xsi:type으로 변환
    for child in list(elem):
        if child.tag == "type":
            # 부모 요소에 xsi:type 속성 추가
            elem.set("{http://www.w3.org/2001/XMLSchema-instance}type", camel_to_snake(child.text))
            # <type> 태그 삭제
            elem.remove(child)
        # 재귀적으로 자식 요소들도 검사
        convert_type_to_xsi_type(child)

def add_namespace_and_type(xml_str):
    # 'xmlns:xsi'와 'xsi:type' 속성 추가 (its_elements와 project)
    xml_str = xml_str.replace(
        '<its_elements>', 
        '<its_elements xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:type="machining_workingstep">'
    )
    xml_str = xml_str.replace(
        '<project>', 
        '<project xmlns="http://www.digital-thread.re/iso14649">'
    )
    return xml_str

def dict_to_xml(parent, data):
    for key, value in data.items():
        attributes = {}

        # 속성 값 (`@`로 시작하는 키)를 분리하여 attributes에 저장
        if isinstance(value, dict):
            keys_to_remove = []
            for attr_key in value.keys():
                if attr_key.startswith("@"):
                    attr_name = attr_key[1:]
                    attributes[attr_name] = value[attr_key]
                    keys_to_remove.append(attr_key)
            for attr_key in keys_to_remove:
                del value[attr_key]

        # 같은 태그 반복 생성 + 재귀 호출
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




def create_feature_xml(json_data: Dict[str, Any], mapping_data: dict, dataclass_type = MachiningWorkingstep): # mapping_config: Dict[str, str], 
    nested_structure = {
        "its_id": {},
        "its_secplane": {},
        "its_feature": {},
        "its_operation": {},
        "its_effect": {}
    }
    
    for json_key, dataclass_path in mapping_data.items():
        path_parts = dataclass_path.split(".")
        current_type = dataclass_type
        parent = nested_structure
        grand_parent = None  # 한 단계 위 부모 저장
        prev_key = None  # 직전 키 저장

        for i, part in enumerate(path_parts):
            if part[0].isupper():  # 현재 요소가 대문자로 시작하는 경우 (클래스)
                if part in globals():  
                    new_type = globals()[part]

                    if isinstance(new_type, type): 
                        if prev_key and prev_key[0].isupper():  # 이전 키가 대문자였을 경우 (대문자가 연속으로 나온 경우) 클래스 가져오기
                            parent_type = globals().get(prev_key)
                            if parent_type and isinstance(parent_type, type) and issubclass(new_type, parent_type):
                                current_type = new_type
                        else:
                            current_type = new_type
            else:
                if hasattr(current_type, "__dataclass_fields__") and part in current_type.__dataclass_fields__:
                    if part not in parent:
                        parent[part] = {}

                if prev_key is not None and grand_parent is not None:  # grand_parent 설정 후 xsi:type 추가
                    name = camel_to_snake(current_type.__name__)
                    if name.startswith("two5_d"): name = name.replace("two5_d", "two5D", 1) # 예외 처리
                    grand_parent[prev_key]["@xsi:type"] = name

                if i == len(path_parts) - 1: 
                    value = get_nested_value(json_data, json_key.split("."))

                    if hasattr(current_type, "__dataclass_fields__") and part in current_type.__dataclass_fields__:
                        field_type = current_type.__dataclass_fields__[part].type 
                        if isinstance(field_type, type) and issubclass(field_type, Enum):
                            if isinstance(value, str): 
                                try:
                                    value = field_type[value]  
                                except KeyError:
                                    raise ValueError(f"Invalid value '{value}' for enum {field_type.__name__}")
                    parent[part] = value
                                    

                grand_parent = parent  # 현재 parent를 grand_parent로 저장
                prev_key = part  # 현재 필드를 부모로 설정
                parent = parent[part]
    root = ET.Element("its_elements", {
        "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
        "xsi:type": "machining_workingstep"
    })
    
    dict_to_xml(root, nested_structure)
    return ET.tostring(root, encoding="unicode", method="xml")

def get_nested_value(data: Dict[str, Any], keys: list):
    for key in keys:
        if isinstance(data, dict) and key in data:
            data = data[key]
        else:
            return None
    return data

def update_xml_from_dataclass(existing_xml_str: str, validated_data: Any) -> str:
    existing_dict = xmltodict.parse(existing_xml_str)
    existing_dict = {k: v for k, v in existing_dict["project"].items() if not k.startswith("@")}

    validated_dict = dataclass_to_dict(validated_data)    

    merged_dict = merge_dicts(existing_dict, validated_dict)
    
    root = ET.Element("project", {
        "xmlns": "http://digital-thread.re/iso14649",
    })
    dict_to_xml(root, merged_dict)

    return ET.tostring(root, encoding="utf-8", xml_declaration=True).decode("utf-8")

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
            merged[key] = [merge_dicts(original_value, update_value[0])] if update_value else [original_value]
            continue
        if isinstance(original_value, list) and isinstance(update_value, dict):
            merged[key] = [merge_dicts(update_value, original_value[0])] if original_value else [update_value]
            continue

        # 리스트끼리 병합
        if isinstance(original_value, list) and isinstance(update_value, list):
            merged[key] = [merge_dicts(o, u) if isinstance(o, dict) and isinstance(u, dict) else u
                           for o, u in zip(original_value, update_value)]
            continue
        
        merged[key] = update_value

    return merged
