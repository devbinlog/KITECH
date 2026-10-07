import { describe, it, expect } from "vitest";
import { convertAvailabilityToTasks } from "@/hooks/useScheduler";

describe("convertAvailabilityToTasks", () => {
  const horizonStart = "2024-06-15T06:00:00Z";
  const dayStartMs = new Date(horizonStart).getTime();

  it("converts availability slots to Gantt tasks with correct fields", () => {
    const availability = [
      {
        equipment_id: "CNC-001",
        equipment_name: "CNC Machine 1",
        schedule: [
          {
            slot_start: "2024-06-15T07:00:00Z",
            slot_end: "2024-06-15T09:00:00Z",
            status: "RUNNING" as const,
            work_order_id: 42,
            lot_no: "LOT-001",
            product: "Widget A",
          },
        ],
      },
    ];

    const tasks = convertAvailabilityToTasks(availability, horizonStart);

    expect(tasks).toHaveLength(1);
    const task = tasks[0];
    expect(task.wo_id).toBe("WO-42");
    expect(task.machine_id).toBe("CNC-001");
    expect(task.lot_no).toBe("LOT-001");
    expect(task.product_name).toBe("Widget A");
    expect(task.status).toBe("RUNNING");
    expect(task.job_id).toBe("LOT-001");
    expect(task.op_id).toMatch(/^OP-CNC-001-1$/);
    // 1 hour = 3600 seconds after horizon start
    expect(task.start_time).toBe(3600);
    // 3 hours = 10800 seconds after horizon start
    expect(task.end_time).toBe(10800);
  });

  it("returns empty array for empty availability", () => {
    const tasks = convertAvailabilityToTasks([], horizonStart);
    expect(tasks).toEqual([]);
  });

  it("returns empty array when equipment has no schedule", () => {
    const availability = [
      {
        equipment_id: "CNC-001",
        equipment_name: "CNC Machine 1",
        // schedule is undefined
      },
    ];

    const tasks = convertAvailabilityToTasks(availability as any, horizonStart);
    expect(tasks).toEqual([]);
  });

  it("skips slots with null slot_start", () => {
    const availability = [
      {
        equipment_id: "CNC-001",
        equipment_name: "CNC Machine 1",
        schedule: [
          {
            slot_start: null,
            slot_end: "2024-06-15T09:00:00Z",
            status: "READY" as const,
            work_order_id: 1,
          },
        ],
      },
    ];

    const tasks = convertAvailabilityToTasks(availability, horizonStart);
    expect(tasks).toHaveLength(0);
  });

  it("skips slots with null slot_end", () => {
    const availability = [
      {
        equipment_id: "CNC-001",
        equipment_name: "CNC Machine 1",
        schedule: [
          {
            slot_start: "2024-06-15T07:00:00Z",
            slot_end: null,
            status: "READY" as const,
            work_order_id: 1,
          },
        ],
      },
    ];

    const tasks = convertAvailabilityToTasks(availability, horizonStart);
    expect(tasks).toHaveLength(0);
  });

  it("clamps negative start times to 0 (slot before horizon)", () => {
    const availability = [
      {
        equipment_id: "CNC-001",
        equipment_name: "CNC Machine 1",
        schedule: [
          {
            slot_start: "2024-06-15T05:00:00Z", // 1 hour BEFORE horizon
            slot_end: "2024-06-15T07:00:00Z",   // 1 hour after horizon
            status: "RUNNING" as const,
            work_order_id: 10,
            lot_no: "LOT-EARLY",
            product: "Early Widget",
          },
        ],
      },
    ];

    const tasks = convertAvailabilityToTasks(availability, horizonStart);

    expect(tasks).toHaveLength(1);
    // start_time would be -3600 but gets clamped to 0
    expect(tasks[0].start_time).toBe(0);
    // end_time is 1 hour = 3600s after horizon
    expect(tasks[0].end_time).toBe(3600);
  });

  it("handles multiple equipment with multiple slots", () => {
    const availability = [
      {
        equipment_id: "CNC-001",
        equipment_name: "CNC Machine 1",
        schedule: [
          {
            slot_start: "2024-06-15T07:00:00Z",
            slot_end: "2024-06-15T08:00:00Z",
            status: "RUNNING" as const,
            work_order_id: 1,
            lot_no: "LOT-A",
            product: "Product A",
          },
          {
            slot_start: "2024-06-15T08:00:00Z",
            slot_end: "2024-06-15T09:00:00Z",
            status: "READY" as const,
            work_order_id: 2,
            lot_no: "LOT-B",
            product: "Product B",
          },
        ],
      },
      {
        equipment_id: "CNC-002",
        equipment_name: "CNC Machine 2",
        schedule: [
          {
            slot_start: "2024-06-15T06:30:00Z",
            slot_end: "2024-06-15T10:00:00Z",
            status: "RUNNING" as const,
            work_order_id: 3,
            lot_no: "LOT-C",
            product: "Product C",
          },
        ],
      },
    ];

    const tasks = convertAvailabilityToTasks(availability, horizonStart);

    expect(tasks).toHaveLength(3);
    // First equipment, slot 1
    expect(tasks[0].machine_id).toBe("CNC-001");
    expect(tasks[0].op_id).toMatch(/^OP-CNC-001-1$/);
    expect(tasks[0].wo_id).toBe("WO-1");
    // First equipment, slot 2
    expect(tasks[1].machine_id).toBe("CNC-001");
    expect(tasks[1].op_id).toMatch(/^OP-CNC-001-2$/);
    expect(tasks[1].wo_id).toBe("WO-2");
    // Second equipment, slot 1 — op_id includes equipment_id for uniqueness
    expect(tasks[2].machine_id).toBe("CNC-002");
    expect(tasks[2].op_id).toMatch(/^OP-CNC-002-1$/);
    expect(tasks[2].wo_id).toBe("WO-3");
    // Uniqueness: all op_ids must be distinct across equipment
    const opIds = tasks.map((t) => t.op_id);
    expect(new Set(opIds).size).toBe(opIds.length);
  });

  it("uses empty string for job_id when lot_no is missing", () => {
    const availability = [
      {
        equipment_id: "CNC-001",
        equipment_name: "CNC Machine 1",
        schedule: [
          {
            slot_start: "2024-06-15T07:00:00Z",
            slot_end: "2024-06-15T08:00:00Z",
            status: "READY" as const,
            work_order_id: 5,
            // lot_no is undefined
          },
        ],
      },
    ];

    const tasks = convertAvailabilityToTasks(availability, horizonStart);

    expect(tasks).toHaveLength(1);
    expect(tasks[0].job_id).toBe("");
    expect(tasks[0].lot_no).toBeUndefined();
  });
});
