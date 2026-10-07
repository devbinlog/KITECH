"""In-memory Machine Data Store.

Singleton store for all machine data. Loads initial data from JSON,
provides get/set operations with address parser integration.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..schemas import (
    WRITABLE_FIELDS,
    PLC_WRITABLE_TYPES,
    MachineData,
    PlcData,
    DataResponse,
    PlcResponse,
)
from .address_parser import (
    parse_address,
    resolve_value,
    _find_parents,
)

# Re-export for address_parser circular reference
__all__ = ["MachineStore", "WRITABLE_FIELDS"]


class MachineStore:
    """In-memory store for machine data."""

    def __init__(self) -> None:
        self.machines: Dict[int, MachineData] = {}

    def load_from_json(self, path: str | Path) -> None:
        """Load machine data from a JSON file."""
        path = Path(path)
        with open(path) as f:
            data = json.load(f)

        if isinstance(data, list):
            for m in data:
                machine = MachineData(**m)
                self.machines[machine.machineId] = machine
        elif isinstance(data, dict) and "machines" in data:
            for m in data["machines"]:
                machine = MachineData(**m)
                self.machines[machine.machineId] = machine
        else:
            machine = MachineData(**data)
            self.machines[machine.machineId] = machine

    def get_machine(self, machine_id: int) -> Optional[MachineData]:
        """Get a machine by ID."""
        return self.machines.get(machine_id)

    def list_machines(self) -> List[Dict[str, Any]]:
        """List all machines (summary)."""
        result = []
        for m in self.machines.values():
            result.append(
                {
                    "machineId": m.machineId,
                    "machineName": m.machineName,
                    "vendorId": m.vendorId,
                    "vendorName": m.vendorName,
                    "modelName": m.modelName,
                    "channels": len(m.channel),
                }
            )
        return result

    def get_value(self, address: str, filter_str: str = "") -> DataResponse:
        """Get data using TORUS address format.

        Args:
            address: e.g. "data://machine/channel/axis/machinePosition"
            filter_str: e.g. "machine=1&channel=1&axis=1"
        """
        parsed = parse_address(address, filter_str)

        # Determine which machine
        machine_ids = parsed.filters.get("machine", [1])

        all_values = []
        for mid in machine_ids:
            machine = self.machines.get(mid)
            if not machine:
                return DataResponse(
                    address=address,
                    filter=filter_str,
                    success=False,
                    error=f"Machine {mid} not found",
                )

            results = resolve_value(machine, parsed)
            all_values.extend(results)

        # Flatten results
        if not all_values:
            return DataResponse(
                address=address,
                filter=filter_str,
                success=False,
                error="No values resolved",
            )

        # Check for errors
        errors = [r for r in all_values if not r.success]
        if errors:
            return DataResponse(
                address=address,
                filter=filter_str,
                success=False,
                error=errors[0].error,
            )

        # Single vs multiple results
        if len(all_values) == 1:
            return DataResponse(
                address=address,
                filter=filter_str,
                value=all_values[0].value,
            )

        return DataResponse(
            address=address,
            filter=filter_str,
            value=[r.value for r in all_values],
        )

    def set_value(self, address: str, filter_str: str = "", value: Any = None) -> DataResponse:
        """Set data using TORUS address format.

        Only writable fields can be modified.
        """
        parsed = parse_address(address, filter_str)
        leaf_field = parsed.leaf

        # Check write permission
        if leaf_field not in WRITABLE_FIELDS:
            return DataResponse(
                address=address,
                filter=filter_str,
                success=False,
                error=f"Field '{leaf_field}' is read-only",
            )

        # Determine which machine
        machine_ids = parsed.filters.get("machine", [1])
        set_count = 0

        for mid in machine_ids:
            machine = self.machines.get(mid)
            if not machine:
                return DataResponse(
                    address=address,
                    filter=filter_str,
                    success=False,
                    error=f"Machine {mid} not found",
                )

            # Find parent objects and set the value
            parents = _find_parents(machine, parsed)
            for parent_obj in parents:
                if hasattr(parent_obj, leaf_field):
                    setattr(parent_obj, leaf_field, value)
                    set_count += 1

        if set_count > 0:
            return DataResponse(
                address=address,
                filter=filter_str,
                value=value,
            )

        return DataResponse(
            address=address,
            filter=filter_str,
            success=False,
            error=f"Could not set '{leaf_field}'",
        )

    def get_plc(
        self, machine_id: int, plc_type: int, start_address: int, count: int
    ) -> PlcResponse:
        """Read PLC memory block."""
        machine = self.machines.get(machine_id)
        if not machine:
            return PlcResponse(
                machine=machine_id,
                type=plc_type,
                startAddress=start_address,
                count=count,
                success=False,
                error=f"Machine {machine_id} not found",
            )

        block = self._get_plc_block(machine.plc, plc_type)
        if block is None:
            return PlcResponse(
                machine=machine_id,
                type=plc_type,
                startAddress=start_address,
                count=count,
                success=False,
                error=f"Invalid PLC type {plc_type}",
            )

        # Extract requested range
        end = start_address + count
        data = block[start_address:end]

        # Pad with zeros if needed
        while len(data) < count:
            data.append(0)

        return PlcResponse(
            machine=machine_id,
            type=plc_type,
            startAddress=start_address,
            count=count,
            data=data,
        )

    def set_plc(
        self, machine_id: int, plc_type: int, start_address: int, data: List[Any]
    ) -> PlcResponse:
        """Write PLC memory block. Only R/W types (2,4,6,8,10) allowed."""
        if plc_type not in PLC_WRITABLE_TYPES:
            return PlcResponse(
                machine=machine_id,
                type=plc_type,
                startAddress=start_address,
                count=len(data),
                success=False,
                error=f"PLC type {plc_type} is read-only. Writable types: {sorted(PLC_WRITABLE_TYPES)}",
            )

        machine = self.machines.get(machine_id)
        if not machine:
            return PlcResponse(
                machine=machine_id,
                type=plc_type,
                startAddress=start_address,
                count=len(data),
                success=False,
                error=f"Machine {machine_id} not found",
            )

        block = self._get_plc_block(machine.plc, plc_type)
        if block is None:
            return PlcResponse(
                machine=machine_id,
                type=plc_type,
                startAddress=start_address,
                count=len(data),
                success=False,
                error=f"Invalid PLC type {plc_type}",
            )

        # Extend block if needed
        needed = start_address + len(data)
        while len(block) < needed:
            block.append(0)

        # Write data
        for i, val in enumerate(data):
            block[start_address + i] = val

        return PlcResponse(
            machine=machine_id,
            type=plc_type,
            startAddress=start_address,
            count=len(data),
            data=data,
        )

    def _get_plc_block(self, plc: PlcData, plc_type: int) -> Optional[list]:
        """Get the appropriate PLC memory block by type number."""
        type_map = {
            1: "rbitBlock",
            2: "bitBlock",
            3: "rbyteBlock",
            4: "byteBlock",
            5: "rwordBlock",
            6: "wordBlock",
            7: "rdwordBlock",
            8: "dwordBlock",
            9: "rqwordBlock",
            10: "qwordBlock",
        }
        attr_name = type_map.get(plc_type)
        if attr_name:
            return getattr(plc, attr_name, None)
        return None


# ─── Singleton ───────────────────────────────────────────────────────────────

_store: Optional[MachineStore] = None


def get_store() -> MachineStore:
    """Get the singleton MachineStore instance."""
    global _store
    if _store is None:
        _store = MachineStore()
    return _store


def reset_store() -> None:
    """Reset the store (for testing)."""
    global _store
    _store = None
