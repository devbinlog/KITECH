import { useQuery } from "@tanstack/react-query";
import { equipmentService } from "@/services/equipment";

export function useMachineTypes() {
  const { data: equipments = [] } = useQuery({
    queryKey: ["equipments"],
    queryFn: () => equipmentService.getAll(),
    staleTime: 5 * 60 * 1000,
  });

  return Array.from(
    new Set(
      equipments
        .map((eq) => (eq.spec_data?.machineType as string) || eq.equipment_type || "")
        .filter(Boolean)
    )
  ).sort();
}
