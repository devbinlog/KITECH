import type { Equipment } from "@/types";

export type EquipmentSourceFilter = "all" | "physical" | "virtual";

function truthyFlag(value: unknown): boolean {
  if (value === true || value === 1) return true;
  if (typeof value !== "string") return false;
  return ["true", "1", "y", "yes"].includes(value.trim().toLowerCase());
}

export function isVirtualEquipment(equipment: Pick<Equipment, "spec_data">): boolean {
  const spec = equipment.spec_data || {};
  const source = String(spec.equipmentSource || "").toUpperCase();
  return truthyFlag(spec.isVirtual) || truthyFlag(spec.is_virtual) || source === "VIRTUAL";
}

export function getEquipmentSourceLabel(equipment: Pick<Equipment, "spec_data">): string {
  return isVirtualEquipment(equipment) ? "가상장비" : "실장비";
}

