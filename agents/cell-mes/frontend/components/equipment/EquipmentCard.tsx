"use client";

import { Equipment } from "@/types";
import { getEquipmentSourceLabel, isVirtualEquipment } from "@/utils/equipment";
import { Cpu, Bot, Truck, CircuitBoard, DoorOpen, GitMerge, Layers, NavigationIcon, Boxes, PackageCheck, ScanLine } from "lucide-react";
import clsx from "clsx";

interface EquipmentCardProps {
  equipment: Equipment;
  onClick?: () => void;
}

const typeIcons = {
  CNC: Cpu,
  ROBOT: Bot,
  AMR: Truck,
  PLC: CircuitBoard,
  RACK: Boxes,
  FEEDER: PackageCheck,
  QCM: ScanLine,
};

const statusColors = {
  RUN: "bg-green-500",
  STOP: "bg-gray-400",
  ERROR: "bg-red-500",
};

const statusLabels = {
  RUN: "가동중",
  STOP: "정지",
  ERROR: "에러",
};

// 도어 상태 한글 변환
const doorStateLabel: Record<string, { label: string; color: string }> = {
  open: { label: "열림", color: "text-orange-500" },
  closed: { label: "닫힘", color: "text-green-600" },
  opening: { label: "열리는 중", color: "text-yellow-500" },
  closing: { label: "닫히는 중", color: "text-yellow-500" },
};

// 바이스(클램프) 상태 한글 변환
const viseStateLabel: Record<string, { label: string; color: string }> = {
  clamp: { label: "클램프", color: "text-green-600" },
  unClamp: { label: "언클램프", color: "text-gray-500" },
  clamping: { label: "클램핑 중", color: "text-yellow-500" },
  unClamping: { label: "언클램핑 중", color: "text-yellow-500" },
};

// 로봇 상태 한글 변환
const robotStatusLabel: Record<string, { label: string; color: string }> = {
  BUSY: { label: "작업중", color: "text-primary-600" },
  IDLE: { label: "대기", color: "text-gray-500" },
  ERROR: { label: "오류", color: "text-red-500" },
  PAUSE: { label: "일시정지", color: "text-yellow-500" },
};

function getSubmodelStatus(lastData: Record<string, any> | null, idShort: string): Record<string, any> | undefined {
  if (!lastData) return undefined;
  const normalizedIdShort = idShort.toLowerCase();
  const matchedKey = Object.keys(lastData).find((key) => key.toLowerCase().startsWith(normalizedIdShort));
  const submodel = matchedKey ? lastData[matchedKey] : undefined;
  return submodel?.status || submodel?.Status;
}

export function EquipmentCard({ equipment, onClick }: EquipmentCardProps) {
  const Icon = typeIcons[equipment.equipment_type as keyof typeof typeIcons] || Cpu;
  const statusColor = statusColors[equipment.current_status as keyof typeof statusColors] || "bg-gray-400";
  const statusLabel = statusLabels[equipment.current_status as keyof typeof statusLabels] || equipment.current_status;
  const isVirtual = isVirtualEquipment(equipment);
  const machineType = equipment.spec_data?.machineType;

  // 미들웨어 submodel 데이터 추출
  const lastData = equipment.last_data as Record<string, any> | null;
  const cncGateway = getSubmodelStatus(lastData, "cncGateway");
  const modbusGateway = getSubmodelStatus(lastData, "modbusGateway");
  const robotGateway = getSubmodelStatus(lastData, "robotGateway");
  const workInfo = lastData?.workInformation || lastData?.WorkInformation;

  const doorState = cncGateway?.doorState ?? cncGateway?.DoorState;
  const viseState = modbusGateway?.viseState ?? modbusGateway?.ViseState;
  const robotStatus = robotGateway?.status;
  const agvPositionX = robotGateway?.agvPositionX ?? robotGateway?.AgvPositionX;
  const agvPositionY = robotGateway?.agvPositionY ?? robotGateway?.AgvPositionY;
  const machinePositionX = cncGateway?.machinePositionX ?? cncGateway?.MachinePositionX;
  const agvX = agvPositionX != null ? Number(agvPositionX) : undefined;
  const agvY = agvPositionY != null ? Number(agvPositionY) : undefined;
  const machineX = machinePositionX != null ? Number(machinePositionX) : undefined;
  const currentWorkId = workInfo?.currentWorkId || workInfo?.CurrentWorkId;

  // 실제로 표시할 항목이 있는지 체크
  const hasDetailData = doorState != null || viseState != null || robotStatus != null || agvX != null || machineX != null;

  return (
    <div
      onClick={onClick}
      className={clsx(
        "card cursor-pointer hover:shadow-md transition-shadow",
        "border-l-4",
        equipment.current_status === "RUN" && "border-l-green-500",
        equipment.current_status === "STOP" && "border-l-gray-400",
        equipment.current_status === "ERROR" && "border-l-red-500",
        !["RUN", "STOP", "ERROR"].includes(equipment.current_status) && "border-l-gray-300"
      )}
    >
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-gray-100 rounded-lg">
            <Icon size={24} className="text-gray-600" />
          </div>
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <h3 className="font-semibold text-gray-800">{equipment.eq_name}</h3>
              <span
                className={clsx(
                  "px-1.5 py-0.5 rounded text-[11px] font-semibold",
                  isVirtual
                    ? "bg-indigo-50 text-indigo-700 border border-indigo-100"
                    : "bg-gray-100 text-gray-600 border border-gray-200"
                )}
              >
                {getEquipmentSourceLabel(equipment)}
              </span>
            </div>
            <p className="text-sm text-gray-500">
              {equipment.equipment_type}
              {machineType && machineType !== equipment.equipment_type && (
                <span className="text-gray-400"> · {machineType}</span>
              )}
            </p>
          </div>
        </div>
        <span
          className={clsx(
            "px-2 py-1 rounded-full text-xs font-medium text-white",
            statusColor
          )}
        >
          {statusLabel}
        </span>
      </div>

      {/* 실제 미들웨어 데이터 기반 상세 정보 */}
      {hasDetailData && (
        <div className="mt-3 space-y-1.5 text-sm">
          {/* CNC 도어 상태 */}
          {doorState != null && (() => {
            const info = doorStateLabel[doorState] || { label: doorState, color: "text-gray-600 bg-gray-100 border-gray-200" };
            return (
              <div className="flex items-center justify-between bg-gray-50/50 p-1.5 rounded">
                <span className="text-gray-500 flex items-center gap-1.5 text-xs font-semibold tracking-wide">
                  <DoorOpen size={14} className="text-primary-400" /> 도어 상태
                </span>
                <span className={`px-2 py-0.5 rounded text-xs font-bold border shadow-sm bg-white ${info.color}`}>{info.label}</span>
              </div>
            );
          })()}

          {/* 바이스(클램프) 상태 */}
          {viseState != null && (() => {
            const info = viseStateLabel[viseState] || { label: viseState, color: "text-gray-600 bg-gray-100 border-gray-200" };
            return (
              <div className="flex items-center justify-between bg-gray-50/50 p-1.5 rounded">
                <span className="text-gray-500 flex items-center gap-1.5 text-xs font-semibold tracking-wide">
                  <Layers size={14} className="text-primary-400" /> 바이스 상태
                </span>
                <span className={`px-2 py-0.5 rounded text-xs font-bold border shadow-sm bg-white ${info.color}`}>{info.label}</span>
              </div>
            );
          })()}

          {/* CNC X축 위치 */}
          {machineX != null && (
            <div className="flex items-center justify-between bg-gray-50/50 p-1.5 rounded">
              <span className="text-gray-500 flex items-center gap-1.5 text-xs font-semibold tracking-wide">
                <GitMerge size={14} className="text-primary-400" /> X축 위치
              </span>
              <span className="font-mono font-medium text-gray-800 text-xs bg-white px-2 py-0.5 rounded shadow-sm border border-gray-100">{machineX.toFixed(1)} mm</span>
            </div>
          )}

          {/* 로봇 상태 */}
          {robotStatus != null && (() => {
            const info = robotStatusLabel[robotStatus] || { label: robotStatus, color: "text-gray-600 bg-gray-100 border-gray-200" };
            return (
              <div className="flex items-center justify-between bg-gray-50/50 p-1.5 rounded">
                <span className="text-gray-500 flex items-center gap-1.5 text-xs font-semibold tracking-wide">
                  <Bot size={14} className="text-primary-400" /> 동작 상태
                </span>
                <span className={`px-2 py-0.5 rounded text-xs font-bold border shadow-sm bg-white ${info.color}`}>{info.label}</span>
              </div>
            );
          })()}

          {/* AGV 위치 */}
          {(agvX != null || agvY != null) && (
            <div className="flex items-center justify-between bg-gray-50/50 p-1.5 rounded">
              <span className="text-gray-500 flex items-center gap-1.5 text-xs font-semibold tracking-wide">
                <NavigationIcon size={14} className="text-primary-400" /> AGV 위치
              </span>
              <span className="font-mono font-medium text-gray-800 text-xs bg-white px-2 py-0.5 rounded shadow-sm border border-gray-100">
                X:{(agvX ?? 0).toFixed(1)} Y:{(agvY ?? 0).toFixed(1)}
              </span>
            </div>
          )}
        </div>
      )}

      {/* 현재 작업 ID */}
      {currentWorkId && (
        <div className="mt-2 px-2 py-1 bg-primary-50 rounded text-xs text-primary-700 truncate" title={currentWorkId}>
          작업중: {currentWorkId}
        </div>
      )}

      {/* AAS ID */}
      {equipment.aas_id && (
        <p className="mt-3 text-xs text-gray-400 truncate" title={equipment.aas_id}>
          AAS: {equipment.aas_id}
        </p>
      )}
    </div>
  );
}
