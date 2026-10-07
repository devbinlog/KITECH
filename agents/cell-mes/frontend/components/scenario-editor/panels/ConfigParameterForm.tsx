"use client";

/**
 * ConfigParameterForm — edit ScenarioConfigData (assets list, AAS path, etc).
 *
 * Design Ref: §5.4 Page UI Checklist > Parameter Panel (ConfigParameterForm)
 */

import { Plus, X } from "lucide-react";

import type { ScenarioAsset, ScenarioConfigData } from "@/types/scenario";

interface Props {
  data: ScenarioConfigData;
  onChange: (patch: Partial<ScenarioConfigData>) => void;
}

export function ConfigParameterForm({ data, onChange }: Props) {
  const updateAsset = (i: number, patch: Partial<ScenarioAsset>) => {
    onChange({
      assets: data.assets.map((a, idx) =>
        idx === i ? { ...a, ...patch } : a
      ),
    });
  };

  const addAsset = () => {
    onChange({
      assets: [...data.assets, { id: "", name: "" }],
    });
  };

  const removeAsset = (i: number) => {
    onChange({ assets: data.assets.filter((_, idx) => idx !== i) });
  };

  return (
    <div className="space-y-3">
      <div>
        <label className="mb-1 block text-[11px] font-semibold uppercase tracking-wider text-gray-700">
          Scenario Name
        </label>
        <input
          type="text"
          value={data.scenarioName}
          onChange={(e) => onChange({ scenarioName: e.target.value })}
          className="w-full rounded border border-gray-300 px-2 py-1 text-xs focus:border-blue-500 focus:outline-none"
        />
      </div>

      <div>
        <label className="mb-1 block text-[11px] font-semibold uppercase tracking-wider text-gray-700">
          AAS File Path
        </label>
        <input
          type="text"
          value={data.aasFilePath}
          onChange={(e) => onChange({ aasFilePath: e.target.value })}
          placeholder="/data/cell1_aas.json"
          className="w-full rounded border border-gray-300 px-2 py-1 font-mono text-xs focus:border-blue-500 focus:outline-none"
        />
      </div>

      <div>
        <label className="mb-1 block text-[11px] font-semibold uppercase tracking-wider text-gray-700">
          Base URL
        </label>
        <input
          type="text"
          value={data.baseUrl}
          onChange={(e) => onChange({ baseUrl: e.target.value })}
          placeholder="http://localhost:8080"
          className="w-full rounded border border-gray-300 px-2 py-1 font-mono text-xs focus:border-blue-500 focus:outline-none"
        />
      </div>

      <div>
        <label className="mb-1 block text-[11px] font-semibold uppercase tracking-wider text-gray-700">
          Assets ({data.assets.length})
        </label>
        <div className="space-y-1">
          {data.assets.map((a, i) => (
            <div key={i} className="flex items-center gap-1">
              <input
                type="text"
                value={a.id}
                onChange={(e) => updateAsset(i, { id: e.target.value })}
                placeholder="ID"
                className="w-20 rounded border border-gray-300 px-1.5 py-0.5 font-mono text-xs focus:border-blue-500 focus:outline-none"
              />
              <input
                type="text"
                value={a.name}
                onChange={(e) => updateAsset(i, { name: e.target.value })}
                placeholder="Name"
                className="flex-1 rounded border border-gray-300 px-1.5 py-0.5 text-xs focus:border-blue-500 focus:outline-none"
              />
              <button
                onClick={() => removeAsset(i)}
                className="rounded p-0.5 text-red-500 hover:bg-red-50"
                title="삭제"
              >
                <X size={12} />
              </button>
            </div>
          ))}
          <button
            onClick={addAsset}
            className="inline-flex items-center gap-1 rounded border border-dashed border-gray-400 px-2 py-0.5 text-xs text-gray-700 hover:border-blue-500 hover:text-blue-700"
          >
            <Plus size={12} /> Add asset
          </button>
        </div>
      </div>
    </div>
  );
}
