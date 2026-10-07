"""Helpers for parsing DT Project ISO14649 XML fragments."""

from dataclasses import dataclass
from typing import Iterable
from xml.etree import ElementTree as ET


@dataclass(frozen=True)
class ParsedWorkplan:
    workplan_id: str
    parent_workplan_id: str | None
    display_name: str | None
    source_path: str
    level: int
    sequence: int
    has_direct_steps: bool
    raw_fragment: str


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def _child_text(element: ET.Element, names: set[str]) -> str | None:
    for child in list(element):
        if _local_name(child.tag) in names and child.text:
            return child.text.strip()
    return None


def _xsi_type(element: ET.Element) -> str | None:
    for key, value in element.attrib.items():
        if _local_name(key) == "type":
            return value.rsplit(":", 1)[-1]
    return None


def _direct_workplan_children(element: ET.Element) -> Iterable[ET.Element]:
    for child in list(element):
        if _local_name(child.tag) == "its_elements" and _xsi_type(child) == "workplan":
            yield child


def _has_direct_steps(element: ET.Element) -> bool:
    for child in list(element):
        if _local_name(child.tag) == "its_elements" and _xsi_type(child) != "workplan":
            return True
    return False


def _workplan_id(element: ET.Element, fallback: str) -> str:
    return (
        _child_text(element, {"its_id", "id"})
        or element.attrib.get("id")
        or element.attrib.get("name")
        or fallback
    )


def _workplan_name(element: ET.Element) -> str | None:
    return _child_text(element, {"name", "its_name", "description"})


def parse_project_workplans(xml_str: str) -> list[ParsedWorkplan]:
    """Parse main_workplan and nested workplans from a DT Project XML string."""
    if not xml_str or not xml_str.strip():
        return []

    root = ET.fromstring(xml_str)
    main_workplan = None
    for element in root.iter():
        if _local_name(element.tag) == "main_workplan":
            main_workplan = element
            break

    if main_workplan is None:
        return []

    parsed: list[ParsedWorkplan] = []

    def visit(element: ET.Element, parent_id: str | None, level: int, source_path: str) -> None:
        index = len(parsed) + 1
        workplan_id = _workplan_id(element, f"workplan_{index}")
        path = f"{source_path}/{workplan_id}" if source_path else workplan_id
        parsed.append(
            ParsedWorkplan(
                workplan_id=workplan_id,
                parent_workplan_id=parent_id,
                display_name=_workplan_name(element),
                source_path=path,
                level=level,
                sequence=index,
                has_direct_steps=_has_direct_steps(element),
                raw_fragment=ET.tostring(element, encoding="unicode"),
            )
        )
        for child in _direct_workplan_children(element):
            visit(child, workplan_id, level + 1, path)

    visit(main_workplan, None, 0, "")
    return parsed
