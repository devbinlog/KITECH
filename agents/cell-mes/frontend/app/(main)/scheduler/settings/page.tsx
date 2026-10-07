"use client";

import { useState, useEffect, useRef } from "react";
import { SlidersHorizontal, Save, RotateCcw, Check, Layers } from "lucide-react";
import { SOLVER_OPTIONS, SCHEDULING_MODES, SchedulingMode } from "@/hooks/useScheduler";

interface SchedulerSettings {
  defaultHorizonHours: number;
  defaultSolver: string;
  timeLimitSec: number;
  defaultMode?: SchedulingMode;
  lotSize: number;
  amrTransferTimeSec: number;
}

const DEFAULT_SETTINGS: SchedulerSettings = {
  defaultHorizonHours: 24,
  defaultSolver: "OR_TOOLS",
  timeLimitSec: 60,
  defaultMode: "new",
  lotSize: 1,
  amrTransferTimeSec: 60,
};

const STORAGE_KEY = "scheduler-settings";

export default function SchedulerSettingsPage() {
  const [settings, setSettings] = useState<SchedulerSettings>(DEFAULT_SETTINGS);
  const [savedSettings, setSavedSettings] = useState<SchedulerSettings>(DEFAULT_SETTINGS);
  const [showSaved, setShowSaved] = useState(false);
  const savedTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Load settings from localStorage
  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      try {
        const parsed = JSON.parse(stored);
        setSettings(parsed);
        setSavedSettings(parsed);
      } catch {
        // ignore parse error
      }
    }
  }, []);

  const hasChanges = JSON.stringify(settings) !== JSON.stringify(savedSettings);

  const handleSave = () => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
    setSavedSettings(settings);
    setShowSaved(true);
    if (savedTimeoutRef.current) clearTimeout(savedTimeoutRef.current);
    savedTimeoutRef.current = setTimeout(() => setShowSaved(false), 2000);
  };

  useEffect(() => {
    return () => {
      if (savedTimeoutRef.current) clearTimeout(savedTimeoutRef.current);
    };
  }, []);

  const handleReset = () => {
    setSettings(DEFAULT_SETTINGS);
    localStorage.removeItem(STORAGE_KEY);
    setSavedSettings(DEFAULT_SETTINGS);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">솔버 설정</h1>
          <p className="text-sm text-gray-500">
            스케줄링 솔버 유형과 파라미터를 관리합니다
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleReset}
            className="btn btn-secondary flex items-center gap-2"
            title="기본값으로 초기화"
          >
            <RotateCcw size={16} />
            초기화
          </button>
          <button
            onClick={handleSave}
            disabled={!hasChanges}
            className={`btn flex items-center gap-2 ${
              hasChanges ? "btn-primary" : "btn-secondary opacity-50 cursor-not-allowed"
            }`}
          >
            {showSaved ? <Check size={16} /> : <Save size={16} />}
            {showSaved ? "저장됨!" : "저장"}
          </button>
        </div>
      </div>

      {/* Settings Form */}
      <div className="card">
        <h2 className="card-header">기본 설정</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 p-4">
          {/* Horizon Hours */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              기본 계획 기간 (시간)
            </label>
            <input
              type="number"
              value={settings.defaultHorizonHours}
              onChange={(e) =>
                setSettings({ ...settings, defaultHorizonHours: parseInt(e.target.value) || 24 })
              }
              min="1"
              max="168"
              className="w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            />
            <p className="text-xs text-gray-500 mt-1">1 ~ 168시간 (최대 7일)</p>
          </div>

          {/* Default Solver */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              기본 솔버
            </label>
            <select
              value={settings.defaultSolver}
              onChange={(e) => setSettings({ ...settings, defaultSolver: e.target.value })}
              className="w-full px-3 py-2 border rounded-md bg-white focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            >
              {SOLVER_OPTIONS.map((solver) => (
                <option key={solver.value} value={solver.value}>
                  {solver.label}
                </option>
              ))}
            </select>
            <p className="text-xs text-gray-500 mt-1">
              {SOLVER_OPTIONS.find(s => s.value === settings.defaultSolver)?.description}
            </p>
          </div>

          {/* Time Limit */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              솔버 시간 제한 (초)
            </label>
            <input
              type="number"
              value={settings.timeLimitSec}
              onChange={(e) =>
                setSettings({ ...settings, timeLimitSec: parseInt(e.target.value) || 60 })
              }
              min="10"
              max="300"
              step="10"
              className="w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            />
            <p className="text-xs text-gray-500 mt-1">10 ~ 300초</p>
          </div>

          {/* Lot Size */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Lot 크기
            </label>
            <input
              type="number"
              value={settings.lotSize}
              onChange={(e) =>
                setSettings({ ...settings, lotSize: parseInt(e.target.value) || 1 })
              }
              min="1"
              className="w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            />
            <p className="text-xs text-gray-500 mt-1">작업지시를 나눌 단위 수량</p>
          </div>

          {/* AMR Transfer Time */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              AMR 이동 시간 (초)
            </label>
            <input
              type="number"
              value={settings.amrTransferTimeSec}
              onChange={(e) =>
                setSettings({ ...settings, amrTransferTimeSec: parseInt(e.target.value) || 60 })
              }
              min="0"
              className="w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            />
            <p className="text-xs text-gray-500 mt-1">설비 간 이동 소요 시간</p>
          </div>

          {/* Default Mode */}
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-2 flex items-center gap-1">
              <Layers size={16} />
              기본 스케줄링 모드
            </label>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {SCHEDULING_MODES.map((mode) => (
                <button
                  key={mode.value}
                  onClick={() => setSettings({ ...settings, defaultMode: mode.value })}
                  className={`p-3 rounded-lg border-2 text-left transition-all ${
                    settings.defaultMode === mode.value
                      ? mode.severity === "danger"
                        ? "border-red-400 bg-red-50"
                        : mode.severity === "warning"
                        ? "border-yellow-400 bg-yellow-50"
                        : "border-primary-400 bg-primary-50"
                      : "border-gray-200 hover:border-gray-300"
                  }`}
                >
                  <p className="font-medium text-sm text-gray-800">{mode.label}</p>
                  <p className="text-xs text-gray-500 mt-0.5">{mode.description}</p>
                </button>
              ))}
            </div>
            <p className="text-xs text-gray-500 mt-1">
              스케줄 실행 페이지에서 사용할 기본 모드
            </p>
          </div>
        </div>
      </div>

      {/* Solver Type Cards */}
      <div className="card">
        <h2 className="card-header">솔버 유형</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 p-4">
          {SOLVER_OPTIONS.map((solver) => (
            <div
              key={solver.value}
              onClick={() => setSettings({ ...settings, defaultSolver: solver.value })}
              className={`p-4 rounded-lg border-2 cursor-pointer transition-all hover:shadow-md ${
                settings.defaultSolver === solver.value
                  ? "border-primary-500 bg-primary-50"
                  : "border-gray-200 hover:border-gray-300"
              }`}
            >
              <div className="flex items-start gap-3">
                <div className={`p-3 rounded-lg ${
                  settings.defaultSolver === solver.value ? "bg-primary-200" : "bg-gray-100"
                }`}>
                  <SlidersHorizontal
                    className={settings.defaultSolver === solver.value ? "text-primary-600" : "text-gray-500"}
                    size={20}
                  />
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <h3 className="font-semibold text-gray-800">{solver.label}</h3>
                    {settings.defaultSolver === solver.value && (
                      <Check size={16} className="text-primary-600" />
                    )}
                  </div>
                  <p className="text-sm text-gray-600 mt-1">{solver.description}</p>
                  <span className="inline-block mt-2 px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded font-mono">
                    {solver.value}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Parameters Reference */}
      <div className="card">
        <h2 className="card-header">파라미터 참조</h2>
        <div className="overflow-x-auto">
          <table className="table">
            <thead>
              <tr>
                <th>파라미터</th>
                <th>설명</th>
                <th>현재값</th>
                <th>범위</th>
              </tr>
            </thead>
            <tbody>
              <tr className={settings.defaultHorizonHours !== DEFAULT_SETTINGS.defaultHorizonHours ? "bg-yellow-50" : ""}>
                <td className="font-mono text-sm">horizon_hours</td>
                <td>계획 기간 (시간)</td>
                <td className="font-semibold">{settings.defaultHorizonHours}</td>
                <td>1 ~ 168</td>
              </tr>
              <tr className={settings.timeLimitSec !== DEFAULT_SETTINGS.timeLimitSec ? "bg-yellow-50" : ""}>
                <td className="font-mono text-sm">time_limit_sec</td>
                <td>솔버 시간 제한 (초)</td>
                <td className="font-semibold">{settings.timeLimitSec}</td>
                <td>10 ~ 300</td>
              </tr>
              <tr className={settings.defaultSolver !== DEFAULT_SETTINGS.defaultSolver ? "bg-yellow-50" : ""}>
                <td className="font-mono text-sm">solver_type</td>
                <td>솔버 알고리즘</td>
                <td className="font-semibold">{settings.defaultSolver}</td>
                <td>위 솔버 목록 참조</td>
              </tr>
              <tr className={settings.defaultMode !== DEFAULT_SETTINGS.defaultMode ? "bg-yellow-50" : ""}>
                <td className="font-mono text-sm">default_mode</td>
                <td>기본 스케줄링 모드</td>
                <td className="font-semibold">{SCHEDULING_MODES.find(m => m.value === settings.defaultMode)?.label || "신규 수립"}</td>
                <td>신규 / 재스케줄 / 전체</td>
              </tr>
              <tr className={settings.lotSize !== DEFAULT_SETTINGS.lotSize ? "bg-yellow-50" : ""}>
                <td className="font-mono text-sm">lot_size</td>
                <td>Lot 분할 단위 수량</td>
                <td className="font-semibold">{settings.lotSize}</td>
                <td>1 이상</td>
              </tr>
              <tr className={settings.amrTransferTimeSec !== DEFAULT_SETTINGS.amrTransferTimeSec ? "bg-yellow-50" : ""}>
                <td className="font-mono text-sm">amr_transfer_time_sec</td>
                <td>AMR 이동 시간 (초)</td>
                <td className="font-semibold">{settings.amrTransferTimeSec}</td>
                <td>0 이상</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* Unsaved Changes Warning */}
      {hasChanges && (
        <div className="fixed bottom-4 right-4 bg-yellow-100 border border-yellow-300 rounded-lg px-4 py-3 shadow-lg flex items-center gap-3">
          <span className="text-yellow-800 text-sm">저장되지 않은 변경사항이 있습니다</span>
          <button onClick={handleSave} className="btn btn-primary btn-sm">
            저장
          </button>
        </div>
      )}
    </div>
  );
}
