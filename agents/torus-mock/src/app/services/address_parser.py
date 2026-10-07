"""TORUS URI Address Parser.

Parses TORUS data addresses like:
  data://machine/channel/axis/machinePosition?machine=1&channel=1&axis=1

Into structured path + filter for resolving values from MachineData model.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class ParsedAddress:
    """Result of parsing a TORUS data address."""

    path_segments: List[str]  # e.g. ["channel", "axis", "machinePosition"]
    filters: Dict[str, List[int]]  # e.g. {"machine": [1], "channel": [1], "axis": [1]}

    @property
    def leaf(self) -> str:
        """Last segment = the target field."""
        return self.path_segments[-1] if self.path_segments else ""


@dataclass
class ResolveResult:
    """Result of resolving a value from MachineData."""

    value: Any = None
    success: bool = True
    error: Optional[str] = None
    path: str = ""


def parse_filter_value(value_str: str) -> List[int]:
    """Parse a filter value that can be a single int, range, or comma-separated list.

    Examples:
        "1"     → [1]
        "1-3"   → [1, 2, 3]
        "1,3,5" → [1, 3, 5]
    """
    value_str = value_str.strip()

    # Range: "1-3"
    range_match = re.match(r"^(\d+)-(\d+)$", value_str)
    if range_match:
        start, end = int(range_match.group(1)), int(range_match.group(2))
        return list(range(start, end + 1))

    # Comma-separated: "1,3,5"
    if "," in value_str:
        return [int(v.strip()) for v in value_str.split(",")]

    # Single value
    return [int(value_str)]


def parse_address(address: str, filter_str: str = "") -> ParsedAddress:
    """Parse a TORUS data address + filter string.

    Args:
        address: e.g. "data://machine/channel/axis/machinePosition"
        filter_str: e.g. "machine=1&channel=1&axis=1"

    Returns:
        ParsedAddress with path segments and parsed filters
    """
    # Strip the data:// prefix
    path = address
    if path.startswith("data://"):
        path = path[len("data://") :]

    # Strip leading "machine/" since MachineData is the root
    if path.startswith("machine/"):
        path = path[len("machine/") :]
    elif path == "machine":
        path = ""

    # Split into segments
    segments = [s for s in path.split("/") if s]

    # Parse filters
    filters: Dict[str, List[int]] = {}
    if filter_str:
        # Handle both URL-encoded and raw & separators
        for pair in filter_str.split("&"):
            if "=" in pair:
                key, val = pair.split("=", 1)
                key = key.strip()
                if key and val.strip():
                    try:
                        filters[key] = parse_filter_value(val)
                    except ValueError:
                        pass  # skip invalid filter values

    return ParsedAddress(path_segments=segments, filters=filters)


def _get_list_item(
    collection: list, index_filter: List[int], filter_name: str
) -> List[Tuple[int, Any]]:
    """Get items from a list using 1-based filter indices.

    Returns list of (0-based-index, item) tuples.
    """
    results = []
    for idx_1based in index_filter:
        idx_0based = idx_1based - 1
        if 0 <= idx_0based < len(collection):
            results.append((idx_0based, collection[idx_0based]))
    return results


def resolve_value(machine_data: Any, parsed: ParsedAddress) -> List[ResolveResult]:
    """Resolve value(s) from a MachineData model using parsed address.

    Uses the path segments to traverse the model hierarchy,
    and filters to select specific items from lists.

    Returns a list of ResolveResult (multiple when filter specifies ranges).
    """
    if not parsed.path_segments:
        # Return entire machine snapshot
        return [
            ResolveResult(
                value=machine_data.model_dump()
                if hasattr(machine_data, "model_dump")
                else machine_data,
                path="machine",
            )
        ]

    # Mapping of path segments to their filter key and attribute name
    LIST_SEGMENTS = {
        "channel": "channel",
        "axis": "axis",
        "spindle": "spindle",
        "workStatus": "workStatus",
        "alarm": "alarm",
        "variable": "variable",
        "workOffset": "workOffset",
        "stream": "stream",
        "magazine": "magazine",
        "tools": "tools",
        "toolEdge": "toolEdge",
        "modal": "modal",
    }

    # Start traversal
    results = []
    _resolve_recursive(
        current=machine_data,
        segments=parsed.path_segments,
        filters=parsed.filters,
        depth=0,
        path_so_far="machine",
        list_segments=LIST_SEGMENTS,
        results=results,
    )

    if not results:
        return [
            ResolveResult(
                success=False,
                error=f"Path not found: {'/'.join(parsed.path_segments)}",
                path="/".join(parsed.path_segments),
            )
        ]

    return results


def _resolve_recursive(
    current: Any,
    segments: List[str],
    filters: Dict[str, List[int]],
    depth: int,
    path_so_far: str,
    list_segments: Dict[str, str],
    results: List[ResolveResult],
) -> None:
    """Recursively resolve path segments."""
    if depth >= len(segments):
        # Reached the leaf
        value = current
        if hasattr(current, "model_dump"):
            value = current.model_dump()
        results.append(ResolveResult(value=value, path=path_so_far))
        return

    segment = segments[depth]
    new_path = f"{path_so_far}/{segment}"

    # Check if this segment is a list-type that needs filter indexing
    if segment in list_segments:
        attr_name = list_segments[segment]
        collection = _get_attr(current, attr_name)

        if collection is None or not isinstance(collection, list):
            results.append(
                ResolveResult(
                    success=False,
                    error=f"'{segment}' is not a list at {path_so_far}",
                    path=new_path,
                )
            )
            return

        # Get filter indices for this segment
        filter_indices = filters.get(segment)
        if filter_indices:
            items = _get_list_item(collection, filter_indices, segment)
        else:
            # No filter → return all items
            items = [(i, item) for i, item in enumerate(collection)]

        if not items:
            results.append(
                ResolveResult(
                    success=False,
                    error=f"No items found for filter {segment}={filters.get(segment)}",
                    path=new_path,
                )
            )
            return

        # If there are more segments, continue traversal into each item
        if depth + 1 < len(segments):
            for idx, item in items:
                item_path = f"{new_path}[{idx + 1}]"
                _resolve_recursive(
                    current=item,
                    segments=segments,
                    filters=filters,
                    depth=depth + 1,
                    path_so_far=item_path,
                    list_segments=list_segments,
                    results=results,
                )
        else:
            # This list segment is the leaf
            for idx, item in items:
                value = item
                if hasattr(item, "model_dump"):
                    value = item.model_dump()
                results.append(
                    ResolveResult(
                        value=value,
                        path=f"{new_path}[{idx + 1}]",
                    )
                )
    else:
        # Regular attribute access
        child = _get_attr(current, segment)
        if child is None:
            # Check if it's a dict key
            if isinstance(current, dict) and segment in current:
                child = current[segment]
            else:
                results.append(
                    ResolveResult(
                        success=False,
                        error=f"Attribute '{segment}' not found at {path_so_far}",
                        path=new_path,
                    )
                )
                return

        if depth + 1 >= len(segments):
            # This is the leaf
            value = child
            if hasattr(child, "model_dump"):
                value = child.model_dump()
            results.append(ResolveResult(value=value, path=new_path))
        else:
            _resolve_recursive(
                current=child,
                segments=segments,
                filters=filters,
                depth=depth + 1,
                path_so_far=new_path,
                list_segments=list_segments,
                results=results,
            )


def _get_attr(obj: Any, name: str) -> Any:
    """Get attribute from object (supports both Pydantic models and dicts)."""
    if hasattr(obj, name):
        return getattr(obj, name)
    if isinstance(obj, dict):
        return obj.get(name)
    return None


def set_value(current: Any, parsed: ParsedAddress, value: Any) -> ResolveResult:
    """Set a value in the MachineData model using parsed address.

    Only writable fields can be set (checked by caller).
    """
    from .machine_store import WRITABLE_FIELDS

    leaf_field = parsed.leaf

    if leaf_field not in WRITABLE_FIELDS:
        return ResolveResult(
            success=False,
            error=f"Field '{leaf_field}' is read-only",
            path="/".join(parsed.path_segments),
        )

    # Navigate to the parent of the leaf
    if len(parsed.path_segments) <= 1:
        # Direct attribute on machine
        if hasattr(current, leaf_field):
            setattr(current, leaf_field, value)
            return ResolveResult(value=value, path=leaf_field)
        return ResolveResult(
            success=False,
            error=f"Attribute '{leaf_field}' not found",
            path=leaf_field,
        )

    # Navigate to parent
    parent_segments = parsed.path_segments[:-1]
    parent_parsed = ParsedAddress(path_segments=parent_segments, filters=parsed.filters)
    parent_results = resolve_value(current, parent_parsed)

    if not parent_results or not parent_results[0].success:
        return ResolveResult(
            success=False,
            error=f"Parent path not found: {'/'.join(parent_segments)}",
            path="/".join(parsed.path_segments),
        )

    # Set the value on each resolved parent
    set_count = 0
    for parent_result in parent_results:
        parent_obj = parent_result.value
        # We need the actual model object, not the dict
        # Re-resolve to get the actual object
        pass

    # Re-traverse to find actual parent objects (not dicts)
    parents = _find_parents(current, parsed)
    for parent_obj in parents:
        if hasattr(parent_obj, leaf_field):
            setattr(parent_obj, leaf_field, value)
            set_count += 1

    if set_count > 0:
        return ResolveResult(
            value=value,
            path="/".join(parsed.path_segments),
        )

    return ResolveResult(
        success=False,
        error=f"Could not set '{leaf_field}'",
        path="/".join(parsed.path_segments),
    )


def _find_parents(root: Any, parsed: ParsedAddress) -> List[Any]:
    """Find the actual parent Pydantic model objects for setting values."""
    LIST_SEGMENTS = {
        "channel": "channel",
        "axis": "axis",
        "spindle": "spindle",
        "workStatus": "workStatus",
        "alarm": "alarm",
        "variable": "variable",
        "workOffset": "workOffset",
        "stream": "stream",
        "magazine": "magazine",
        "tools": "tools",
        "toolEdge": "toolEdge",
        "modal": "modal",
    }

    parent_segments = parsed.path_segments[:-1]
    if not parent_segments:
        return [root]

    current_objects = [root]

    for seg in parent_segments:
        next_objects = []
        for obj in current_objects:
            if seg in LIST_SEGMENTS:
                attr_name = LIST_SEGMENTS[seg]
                collection = _get_attr(obj, attr_name)
                if collection and isinstance(collection, list):
                    filter_indices = parsed.filters.get(seg)
                    if filter_indices:
                        for idx_1based in filter_indices:
                            idx_0based = idx_1based - 1
                            if 0 <= idx_0based < len(collection):
                                next_objects.append(collection[idx_0based])
                    else:
                        next_objects.extend(collection)
            else:
                child = _get_attr(obj, seg)
                if child is not None:
                    next_objects.append(child)

        current_objects = next_objects

    return current_objects
