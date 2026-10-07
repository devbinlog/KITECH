"""
AAS Loader

Reads scheduler configuration from Asset Administration Shell JSON.
Parses each asset's schedulerInfo submodel to build Machine, AMRConfig,
MachineTypeParams, and SchedulerConfig objects.

Convention (set in schedulerInfo submodel):
  - machineType == "AMR"     → AMRConfig
  - machineType != "AMR"     → Machine (VMC_3AXIS_MASS, VMC_3AXIS_PALLET, RACK 등)
"""

import json
import logging
from datetime import datetime, time as dtime
from pathlib import Path
from typing import Dict, List, Optional

try:
    from ...solvers import (
        AMRConfig,
        Break,
        Calendar,
        Machine,
        MachineTypeParams,
        OccupiedSlot,
    )
except ImportError:
    from solvers import (  # noqa: E402 – direct import when src/ is in sys.path
        AMRConfig,
        Break,
        Calendar,
        Machine,
        MachineTypeParams,
        OccupiedSlot,
    )

logger = logging.getLogger(__name__)


class AASLoader:
    def __init__(self, aas_path: str):
        path = Path(aas_path)
        if not path.exists():
            raise FileNotFoundError(f"AAS file not found: {aas_path}")
        with open(path, encoding="utf-8") as f:
            self.data = json.load(f)

        self._sm_by_id: Dict[str, dict] = {
            sm["id"]: sm for sm in self.data.get("submodels", [])
        }
        n_aas = len(self.data.get("assetAdministrationShells", []))
        logger.info(f"AASLoader: {n_aas} AAS, {len(self._sm_by_id)} submodels from {aas_path}")

    # ------------------------------------------------------------------
    # Public loaders
    # ------------------------------------------------------------------

    def load_machines(self, horizon_start: datetime) -> List[Machine]:
        machines = []
        for aas in self.data.get("assetAdministrationShells", []):
            sched = self._get_scheduler_info(aas)
            if sched is None:
                continue
            elems = sched.get("submodelElements", [])
            machine_type = self._prop(elems, "machineType")
            if machine_type is None or machine_type == "AMR":
                continue  # AMR

            cal_col = self._col(elems, "calendar")
            calendar = self._parse_calendar(cal_col) if cal_col is not None else None

            machines.append(Machine(
                machine_id=aas["id"],
                machine_name=aas["idShort"],
                machine_type=machine_type,
                status=self._prop(elems, "status") or "available",
                available_from=horizon_start,
                current_setup_id=self._prop(elems, "currentSetupId"),
                setup_change_time_min=int(self._prop(elems, "setupChangeTimeMin") or 0),
                occupied_slots=[],
                calendar=calendar,
            ))
            logger.debug(f"  machine: {aas['idShort']} type={machine_type}")

        logger.info(f"AASLoader.load_machines → {len(machines)} machines")
        return machines

    def load_machine_type_params(self) -> Dict[str, MachineTypeParams]:
        params: Dict[str, MachineTypeParams] = {}
        for aas in self.data.get("assetAdministrationShells", []):
            sched = self._get_scheduler_info(aas)
            if sched is None:
                continue
            elems = sched.get("submodelElements", [])
            machine_type = self._prop(elems, "machineType")
            if machine_type is None or machine_type == "AMR" or machine_type in params:
                continue

            p_col = self._col(elems, "machineTypeParams")
            if p_col is not None:
                params[machine_type] = MachineTypeParams(
                    loading_type=self._prop(p_col, "loadingType") or "direct",
                    amr_transport_qty=int(self._prop(p_col, "amrTransportQty") or 1),
                    exchange_time_sec=int(self._prop(p_col, "exchangeTimeSec") or 0),
                    load_unload_time_sec=int(self._prop(p_col, "loadUnloadTimeSec") or 0),
                )

        logger.info(f"AASLoader.load_machine_type_params → {list(params.keys())}")
        return params

    def load_amrs(self) -> List[AMRConfig]:
        amrs = []
        for aas in self.data.get("assetAdministrationShells", []):
            sched = self._get_scheduler_info(aas)
            if sched is None:
                continue
            elems = sched.get("submodelElements", [])
            if self._prop(elems, "machineType") != "AMR":
                continue  # Machine

            acc_col = self._col(elems, "accessibleMachines")
            accessible = [
                item["value"]
                for item in (acc_col or [])
                if item.get("modelType") == "Property" and item.get("value")
            ]

            amrs.append(AMRConfig(
                amr_id=aas["id"],
                model=self._prop(elems, "model") or "",
                status=self._prop(elems, "status") or "available",
                current_location="",
                accessible_machines=accessible,
                speed_m_per_sec=float(self._prop(elems, "speedMPerSec") or 1.0),
            ))
            logger.debug(f"  AMR: {aas['idShort']}")

        logger.info(f"AASLoader.load_amrs → {len(amrs)} AMRs")
        return amrs

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _get_scheduler_info(self, aas: dict) -> Optional[dict]:
        for ref in aas.get("submodels", []):
            sm_id = ref["keys"][0]["value"]
            sm = self._sm_by_id.get(sm_id)
            if sm and sm.get("idShort") == "schedulerInfo":
                return sm
        return None

    @staticmethod
    def _prop(elements: list, idshort: str) -> Optional[str]:
        for elem in elements:
            if elem.get("idShort") == idshort and elem.get("modelType") == "Property":
                return elem.get("value")
        return None

    @staticmethod
    def _col(elements: list, idshort: str) -> Optional[list]:
        for elem in elements:
            if elem.get("idShort") == idshort and elem.get("modelType") == "SubmodelElementCollection":
                return elem.get("value") or []
        return None

    def _parse_calendar(self, cal_elements: list) -> Calendar:
        start_str = self._prop(cal_elements, "shiftStart") or "08:00"
        end_str = self._prop(cal_elements, "shiftEnd") or "20:00"
        sh, sm_ = (int(x) for x in start_str.split(":"))
        eh, em = (int(x) for x in end_str.split(":"))

        breaks = []
        breaks_col = self._col(cal_elements, "breaks")
        for item in (breaks_col or []):
            if item.get("modelType") != "SubmodelElementCollection":
                continue
            be = item.get("value", [])
            bstart = self._prop(be, "start") or ""
            bend = self._prop(be, "end") or ""
            if bstart and bend:
                bsh, bsm = (int(x) for x in bstart.split(":"))
                beh, bem = (int(x) for x in bend.split(":"))
                breaks.append(Break(start=dtime(bsh, bsm), end=dtime(beh, bem)))

        return Calendar(shift_start=dtime(sh, sm_), shift_end=dtime(eh, em), breaks=breaks)
