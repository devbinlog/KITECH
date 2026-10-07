"use client";

/**
 * RunStatusIndicator — toolbar pill showing the current run status.
 *
 * Design Ref: §5.4 SaveStatusIndicator + RunStatusIndicator pair
 */

import { useExecutionStore } from "../store/useExecutionStore";

export function RunStatusIndicator() {
  const status = useExecutionStore((s) => s.status);
  const finishedAt = useExecutionStore((s) => s.finishedAt);

  if (status === "idle") {
    return <span className="text-xs text-gray-400">실행 대기</span>;
  }
  if (status === "queued") {
    return <span className="text-xs text-blue-500">대기 중...</span>;
  }
  if (status === "running") {
    return <span className="text-xs text-blue-600">▶ 실행 중...</span>;
  }
  if (status === "success") {
    const t = finishedAt
      ? new Date(finishedAt).toLocaleTimeString("ko-KR", {
          hour: "2-digit",
          minute: "2-digit",
          second: "2-digit",
        })
      : "";
    return <span className="text-xs text-green-600">✓ 완료 {t}</span>;
  }
  if (status === "error") {
    return <span className="text-xs text-red-600">✗ 실패</span>;
  }
  return <span className="text-xs text-gray-500">⏹ 취소됨</span>;
}
