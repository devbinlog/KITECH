"use client";

import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { productionService } from "@/services/production";
import { WorkOrder } from "@/types";
import { X, AlertCircle, Play, CheckCircle, Clock } from "lucide-react";
import { POLLING } from "@/config/constants";

interface LotMonitoringModalProps {
    order: WorkOrder;
    onClose: () => void;
}

export default function LotMonitoringModal({ order, onClose }: LotMonitoringModalProps) {
    const queryClient = useQueryClient();

    // Fetch monitoring data
    const { data: monitoring, isLoading, isError, error } = useQuery({
        queryKey: ["order-monitoring", order.id],
        queryFn: () => productionService.getMonitoring(order.id),
        refetchInterval: POLLING.FAST, // 3 seconds
        enabled: !!order.id && (order.status === "RUNNING" || order.status === "PAUSE" || order.status === "ERROR"),
    });

    // Action mutations
    const resumeMutation = useMutation({
        mutationFn: (unitNo: number) => productionService.resumeMiddlewareUnit(order.id, unitNo, {
            mode: "CURRENT_STEP",
            clear_retry: true,
        }),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["order-monitoring", order.id] });
            queryClient.invalidateQueries({ queryKey: ["order-middleware-state", order.id] });
        },
    });

    const clearAlarmMutation = useMutation({
        mutationFn: (unitNo: number) => productionService.commandMiddlewareUnit(order.id, unitNo, "clear-alarm"),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["order-monitoring", order.id] });
            queryClient.invalidateQueries({ queryKey: ["order-middleware-state", order.id] });
        },
    });

    // Extract units list safely
    const units = monitoring?.units || [];
    const statusLabel = monitoring?.status || "UNKNOWN";

    return (
        <div className="fixed inset-0 bg-black/50 flex flex-col items-center justify-center z-[60] p-4">
            <div className="bg-white rounded-lg shadow-2xl w-full max-w-4xl flex flex-col max-h-[90vh]">
                {/* Header */}
                <div className="flex items-center justify-between p-4 border-b shrink-0 bg-gray-50 rounded-t-lg">
                    <div>
                        <h2 className="text-xl font-bold flex items-center gap-2">
                            로트 상세 모니터링
                            <span className="text-sm font-normal text-gray-500 bg-gray-200 px-2 py-0.5 rounded-full">
                                {order.lot_no}
                            </span>
                        </h2>
                        <p className="text-sm text-gray-500 mt-1">
                            미들웨어 상태: <strong className={statusLabel === 'ERROR' ? 'text-red-600' : 'text-primary-600'}>{statusLabel}</strong>
                        </p>
                    </div>
                    <button onClick={onClose} className="p-2 text-gray-400 hover:text-gray-700 hover:bg-gray-200 rounded-full transition-colors">
                        <X size={24} />
                    </button>
                </div>

                {/* Content */}
                <div className="p-6 overflow-y-auto flex-1 bg-gray-50/50">
                    {isLoading ? (
                        <div className="flex justify-center items-center h-40">
                            <span className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></span>
                            <span className="ml-3 text-gray-500">모니터링 데이터를 불러오는 중...</span>
                        </div>
                    ) : isError || monitoring?.status === "NOT_FOUND_IN_MIDDLEWARE" ? (
                        <div className="bg-red-50 text-red-700 p-6 rounded-lg border border-red-200 flex flex-col items-center justify-center text-center h-40">
                            <AlertCircle size={32} className="mb-2 opacity-80" />
                            <p className="font-semibold">모니터링 정보를 확인할 수 없습니다.</p>
                            <p className="text-sm mt-1 opacity-80">
                                {error ? (error as any).message : "미들웨어에서 로트 데이터가 조회되지 않습니다."}
                            </p>
                        </div>
                    ) : units.length === 0 ? (
                        <div className="text-center p-10 bg-gray-100 rounded-lg text-gray-500 text-sm">
                            진행 중인 단위 공정(Unit) 정보가 없습니다.
                        </div>
                    ) : (
                        <div className="space-y-4 relative before:absolute before:inset-0 before:ml-5 before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-gradient-to-b before:from-transparent before:via-slate-200 before:to-transparent">
                            {units.map((unit: any, index: number) => {
                                const isErrorState = unit.status === "ERROR" || unit.status === "ALARM";
                                const isRunning = unit.status === "RUNNING";
                                const isDone = unit.status === "DONE";
                                const isReady = unit.status === "READY";

                                // Determine dot icon/color
                                let Icon = Clock;
                                let dotBg = "bg-gray-200 text-gray-500";
                                let cardBg = "bg-white border-gray-200";

                                if (isErrorState) {
                                    Icon = AlertCircle;
                                    dotBg = "bg-red-500 text-white shadow-[0_0_10px_rgba(239,68,68,0.5)]";
                                    cardBg = "bg-red-50 border-red-300 ring-1 ring-red-500";
                                } else if (isRunning) {
                                    Icon = Play;
                                    dotBg = "bg-primary-500 text-white animate-pulse shadow-[0_0_10px_rgba(59,130,246,0.5)]";
                                    cardBg = "bg-primary-50/50 border-primary-200";
                                } else if (isDone) {
                                    Icon = CheckCircle;
                                    dotBg = "bg-green-500 text-white";
                                    cardBg = "bg-white border-gray-200 opacity-70";
                                }

                                return (
                                    <div key={unit.unit_no} className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group">
                                        {/* Timeline Dot */}
                                        <div className={`flex items-center justify-center w-10 h-10 rounded-full border-4 border-white shadow shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 z-10 ${dotBg}`}>
                                            <Icon size={16} />
                                        </div>

                                        {/* Card */}
                                        <div className="w-[calc(100%-4rem)] md:w-[calc(50%-2.5rem)]">
                                            <div className={`p-4 rounded-xl border shadow-sm transition-all duration-200 hover:shadow-md ${cardBg}`}>
                                                <div className="flex justify-between items-start mb-2">
                                                    <div>
                                                        <span className="text-xs font-bold text-gray-400 uppercase tracking-wider">Unit {unit.unit_no}</span>
                                                        <h3 className="font-semibold text-gray-800 text-lg">{unit.name || `Unit ${unit.unit_no}`}</h3>
                                                    </div>
                                                    <span className={`px-2.5 py-1 rounded-full text-xs font-bold ${isErrorState ? "bg-red-100 text-red-700" :
                                                            isRunning ? "bg-primary-100 text-primary-700" :
                                                                isDone ? "bg-green-100 text-green-700" :
                                                                    "bg-gray-100 text-gray-600"
                                                        }`}>
                                                        {unit.status}
                                                    </span>
                                                </div>

                                                {unit.operation && (
                                                    <div className="text-sm text-gray-600 mb-2 truncate">
                                                        <strong>Operation:</strong> {unit.operation}
                                                    </div>
                                                )}

                                                {/* Progress */}
                                                {unit.progress_total > 0 && (
                                                    <div className="mt-3">
                                                        <div className="flex justify-between text-xs mb-1">
                                                            <span className="text-gray-500 font-medium tracking-wide">PROGRESS</span>
                                                            <span className="font-semibold text-gray-700">{unit.progress_current} / {unit.progress_total}</span>
                                                        </div>
                                                        <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
                                                            <div
                                                                className={`h-full rounded-full transition-all duration-500 ${isErrorState ? 'bg-red-500' : 'bg-primary-500'}`}
                                                                style={{ width: `${Math.min((unit.progress_current / unit.progress_total) * 100, 100)}%` }}
                                                            />
                                                        </div>
                                                    </div>
                                                )}

                                                {/* Alarms and Actions */}
                                                {isErrorState && (
                                                    <div className="mt-4 border-t border-red-200 pt-3">
                                                        <div className="flex gap-2">
                                                            <button
                                                                onClick={() => clearAlarmMutation.mutate(unit.unit_no)}
                                                                disabled={clearAlarmMutation.isPending}
                                                                className="flex-1 btn bg-white text-gray-700 border-gray-300 hover:bg-gray-50 text-sm py-1.5"
                                                            >
                                                                {clearAlarmMutation.isPending ? "요청 중..." : "알람 해제"}
                                                            </button>
                                                        </div>
                                                    </div>
                                                )}

                                                {/* Optional manual resume on PAUSE/idle */}
                                                {unit.status === "STOPPED" && (
                                                    <div className="mt-4 border-t pt-3">
                                                        <button
                                                            onClick={() => resumeMutation.mutate(unit.unit_no)}
                                                            disabled={resumeMutation.isPending}
                                                            className="w-full btn btn-primary text-sm py-1.5"
                                                        >
                                                            {resumeMutation.isPending ? "요청 중..." : "재시작 (Resume)"}
                                                        </button>
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
