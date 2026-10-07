"use client";

/**
 * /master/scenarios/[id]/edit
 *
 * Scenario YAML editor page.
 *
 * V1 (M1) — load, render canvas, save loop, dirty guard
 * V2 (M2) — custom node renderers + RoutingEdge
 * V3 (M3) — ParameterPanel right sidebar; lifted React Flow state
 *
 * Design Ref: §5.1 Screen Layout, §11 M1/M2/M3
 * Plan SC: #1, #2, #11
 */

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import {
  ArrowLeft,
  Save,
  X,
  AlertCircle,
  Undo2,
  Redo2,
  AlignVerticalJustifyCenter,
  Search,
  HelpCircle,
  StickyNote,
  Play,
  StopCircle,
  Download,
  Upload,
  FileJson,
} from "lucide-react";
import {
  ReactFlowProvider,
  useEdgesState,
  useNodesState,
  useReactFlow,
} from "reactflow";

import type { StickyNoteData } from "@/types/scenario";

import { ScenarioCanvas } from "@/components/scenario-editor/canvas/ScenarioCanvas";
import { ParameterPanel } from "@/components/scenario-editor/panels/ParameterPanel";
import { NodeSearchPalette } from "@/components/scenario-editor/panels/NodeSearchPalette";
import { VariableExplorer } from "@/components/scenario-editor/panels/VariableExplorer";
import { ExecutionPanel } from "@/components/scenario-editor/panels/ExecutionPanel";
import { RunStatusIndicator } from "@/components/scenario-editor/toolbar/RunStatusIndicator";
import { YamlPreviewModal } from "@/components/scenario-editor/panels/YamlPreviewModal";
import { useTestRunner } from "@/components/scenario-editor/execution/useTestRunner";
import { useExecutionStore } from "@/components/scenario-editor/store/useExecutionStore";
import { applyEditsToWorkflow } from "@/components/scenario-editor/utils/editorToWorkflow";
import {
  exportWorkflowAsJson,
  importWorkflowFromFile,
} from "@/components/scenario-editor/utils/n8nJsonIO";
import { workflowToEditor } from "@/components/scenario-editor/utils/workflowToEditor";
import { validateAll } from "@/components/scenario-editor/utils/validate";
import type { N8nWorkflow } from "@/types/scenario";
import { KeyboardShortcutsHelp } from "@/components/scenario-editor/toolbar/KeyboardShortcutsHelp";
import { useScenarioLoader } from "@/components/scenario-editor/hooks/useScenarioLoader";
import { useScenarioSaver } from "@/components/scenario-editor/hooks/useScenarioSaver";
import { useUndoRedo } from "@/components/scenario-editor/hooks/useUndoRedo";
import { useAutoSave } from "@/components/scenario-editor/hooks/useAutoSave";
import { useBeforeUnloadGuard } from "@/components/scenario-editor/hooks/useBeforeUnloadGuard";
import { useClipboard } from "@/components/scenario-editor/hooks/useClipboard";
import { useEditorStore } from "@/components/scenario-editor/store/useEditorStore";
import { tidyUp } from "@/components/scenario-editor/utils/tidyUp";
import { scenarioService } from "@/services/master";

// Next.js 14: params is a plain object (not a Promise). The Next.js 15
// `use(params)` pattern is reserved for the upcoming async-params migration.
interface PageProps {
  params: { id: string };
}

export default function ScenarioEditPage({ params }: PageProps) {
  return (
    <ReactFlowProvider>
      <ScenarioEditPageInner params={params} />
    </ReactFlowProvider>
  );
}

function ScenarioEditPageInner({ params }: PageProps) {
  const scenarioId = Number(params.id);
  const router = useRouter();

  const { data, isLoading, error } = useScenarioLoader(scenarioId);
  const saver = useScenarioSaver();
  const dirty = useEditorStore((s) => s.dirty);
  const saveStatus = useEditorStore((s) => s.saveStatus);

  // Lifted React Flow state — Canvas (presentational) and ParameterPanel
  // both read/write through here.
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  // Undo/Redo + keyboard shortcuts
  const {
    pushSnapshot,
    undo,
    redo,
    canUndo,
    canRedo,
    reset: resetHistory,
  } = useUndoRedo({ nodes, edges, setNodes, setEdges });

  // Clipboard: Copy / Cut / Paste / Duplicate / Bulk delete
  useClipboard({ nodes, edges, setNodes, setEdges, pushSnapshot });

  // When loader resolves, hydrate the editor state and clear history.
  useEffect(() => {
    if (data) {
      setNodes(data.nodes);
      setEdges(data.edges);
      resetHistory();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data]);

  const [confirmCancel, setConfirmCancel] = useState(false);

  const handleSave = useCallback(() => {
    if (!data) return;
    saver.mutate({
      scenarioId,
      baseWorkflow: data.workflow,
      nodes,
    });
  }, [data, nodes, saver, scenarioId]);

  // Auto-save (debounced 2s on dirty)
  useAutoSave({
    enabled: !!data && !saver.isPending,
    dirty,
    save: handleSave,
  });

  // Browser-level dirty guard
  useBeforeUnloadGuard(dirty);

  // Validation — recompute on node changes; pushed to editor store so
  // NodeBadge in custom nodes can render without prop drilling.
  useEffect(() => {
    useEditorStore.getState().setErrorsByNodeId(validateAll(nodes));
  }, [nodes]);

  // ----- M6: Tidy up + Search palette + Shortcuts help -----
  const [searchOpen, setSearchOpen] = useState(false);
  const [helpOpen, setHelpOpen] = useState(false);

  const { data: actionsResp } = useQuery({
    queryKey: ["scenario-actions"],
    queryFn: () => scenarioService.getActions(),
    staleTime: Infinity,
  });
  const actions = actionsResp?.data ?? [];

  const handleTidyUp = useCallback(() => {
    pushSnapshot();
    setNodes((nds) => tidyUp(nds, edges));
    useEditorStore.getState().markDirty();
  }, [pushSnapshot, setNodes, edges]);

  // ----- M11: Export / Import / YAML preview -----
  const [yamlModalOpen, setYamlModalOpen] = useState(false);
  const importInputRef =
    useRef<HTMLInputElement | null>(null);

  const buildMergedWorkflow = useCallback((): N8nWorkflow | null => {
    if (!data) return null;
    return applyEditsToWorkflow(data.workflow, nodes);
  }, [data, nodes]);

  const handleExport = useCallback(() => {
    const wf = buildMergedWorkflow();
    if (!wf) return;
    exportWorkflowAsJson(wf, data?.scenarioName ?? `scenario-${scenarioId}`);
  }, [buildMergedWorkflow, data?.scenarioName, scenarioId]);

  const handleImportFile = useCallback(
    async (file: File) => {
      try {
        const imported = await importWorkflowFromFile(file);
        pushSnapshot();
        const { nodes: ns, edges: es } = workflowToEditor(imported);
        setNodes(ns);
        setEdges(es);
        useEditorStore.getState().markDirty();
      } catch (e) {
        const msg =
          e instanceof Error ? e.message : "Import failed";
        useEditorStore
          .getState()
          .setSaveStatus({ kind: "error", message: msg });
      }
    },
    [pushSnapshot, setNodes, setEdges]
  );

  // ----- M10: Test Execution -----
  const runner = useTestRunner(scenarioId);
  const runStatus = useExecutionStore((s) => s.status);
  const handleRun = useCallback(() => {
    if (!data) return;
    const merged = applyEditsToWorkflow(data.workflow, nodes);
    runner.start(merged);
  }, [data, nodes, runner]);

  const rfInstance = useReactFlow();
  const handleAddSticky = useCallback(() => {
    pushSnapshot();
    const center = (() => {
      try {
        return rfInstance.screenToFlowPosition({
          x: window.innerWidth / 2 - 120,
          y: window.innerHeight / 2 - 90,
        });
      } catch {
        return { x: 400, y: 400 };
      }
    })();
    const data: StickyNoteData = {
      kind: "stickyNote",
      text: "",
      width: 240,
      height: 180,
      color: "yellow",
    };
    const newId =
      typeof crypto !== "undefined" && "randomUUID" in crypto
        ? crypto.randomUUID()
        : `sticky-${Date.now().toString(36)}`;
    setNodes((nds) => [
      ...nds,
      { id: newId, type: "stickyNote", position: center, data },
    ]);
    useEditorStore.getState().setSelectedNodeIds([newId]);
    useEditorStore.getState().markDirty();
  }, [pushSnapshot, setNodes, rfInstance]);

  // Bind Ctrl+K (search) and "?" (shortcuts help) globally
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement | null;
      const inField =
        target &&
        (target.tagName === "INPUT" ||
          target.tagName === "TEXTAREA" ||
          target.isContentEditable);
      const mod = e.ctrlKey || e.metaKey;

      if (mod && e.key === "k") {
        e.preventDefault();
        setSearchOpen(true);
        return;
      }
      if (mod && e.key === "s") {
        e.preventDefault();
        if (dirty) handleSave();
        return;
      }
      if (!mod && !inField && e.key === "?") {
        e.preventDefault();
        setHelpOpen((v) => !v);
      }
      if (e.key === "Escape") {
        setSearchOpen(false);
        setHelpOpen(false);
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [dirty, handleSave]);

  const handleCancel = () => {
    if (dirty) {
      setConfirmCancel(true);
      return;
    }
    router.push("/master/scenarios");
  };

  const handleConfirmDiscard = () => {
    setConfirmCancel(false);
    router.push("/master/scenarios");
  };

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center text-gray-600">
        Loading scenario {scenarioId}…
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="flex max-w-lg items-start gap-3 rounded-lg border border-red-200 bg-red-50 p-4">
          <AlertCircle className="mt-0.5 h-5 w-5 text-red-600" />
          <div>
            <div className="font-semibold text-red-900">
              시나리오를 불러올 수 없습니다
            </div>
            <div className="mt-1 text-sm text-red-700">
              {error?.message ?? "Unknown error"}
            </div>
            <button
              onClick={() => router.push("/master/scenarios")}
              className="mt-3 inline-flex items-center gap-1 text-sm text-red-700 hover:text-red-900"
            >
              <ArrowLeft className="h-4 w-4" /> 시나리오 목록으로
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen flex-col">
      {/* Toolbar */}
      <div className="flex items-center justify-between border-b border-gray-200 bg-white px-4 py-2 shadow-sm">
        <div className="flex items-center gap-3">
          <button
            onClick={handleCancel}
            className="inline-flex items-center gap-1 rounded px-2 py-1 text-sm text-gray-700 hover:bg-gray-100"
          >
            <ArrowLeft className="h-4 w-4" />
            <span>뒤로</span>
          </button>
          <div className="text-sm font-semibold text-gray-900">
            {data.scenarioName}
          </div>
          <span className="text-xs text-gray-500">({data.filePath})</span>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={undo}
            disabled={!canUndo}
            title="Undo (Ctrl+Z)"
            className="inline-flex items-center gap-1 rounded border border-gray-300 px-2 py-1.5 text-sm hover:bg-gray-100 disabled:cursor-not-allowed disabled:opacity-40"
          >
            <Undo2 className="h-4 w-4" />
          </button>
          <button
            onClick={redo}
            disabled={!canRedo}
            title="Redo (Ctrl+Y)"
            className="inline-flex items-center gap-1 rounded border border-gray-300 px-2 py-1.5 text-sm hover:bg-gray-100 disabled:cursor-not-allowed disabled:opacity-40"
          >
            <Redo2 className="h-4 w-4" />
          </button>
          <button
            onClick={handleTidyUp}
            title="Tidy up (자동 레이아웃)"
            className="inline-flex items-center gap-1 rounded border border-gray-300 px-2 py-1.5 text-sm hover:bg-gray-100"
          >
            <AlignVerticalJustifyCenter className="h-4 w-4" />
          </button>
          <button
            onClick={handleAddSticky}
            title="Sticky note 추가"
            className="inline-flex items-center gap-1 rounded border border-gray-300 px-2 py-1.5 text-sm hover:bg-gray-100"
          >
            <StickyNote className="h-4 w-4" />
          </button>
          <button
            onClick={handleExport}
            title="n8n JSON으로 내보내기"
            className="inline-flex items-center gap-1 rounded border border-gray-300 px-2 py-1.5 text-sm hover:bg-gray-100"
          >
            <Download className="h-4 w-4" />
          </button>
          <button
            onClick={() => importInputRef.current?.click()}
            title="n8n JSON 가져오기"
            className="inline-flex items-center gap-1 rounded border border-gray-300 px-2 py-1.5 text-sm hover:bg-gray-100"
          >
            <Upload className="h-4 w-4" />
          </button>
          <input
            ref={importInputRef}
            type="file"
            accept="application/json,.json"
            className="hidden"
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) handleImportFile(f);
              // Reset so the same file can be imported again later.
              e.target.value = "";
            }}
          />
          <button
            onClick={() => setYamlModalOpen(true)}
            title="YAML 미리보기"
            className="inline-flex items-center gap-1 rounded border border-gray-300 px-2 py-1.5 text-sm hover:bg-gray-100"
          >
            <FileJson className="h-4 w-4" />
          </button>
          <button
            onClick={() => setSearchOpen(true)}
            title="검색 / 신규 step (Ctrl+K)"
            className="inline-flex items-center gap-1 rounded border border-gray-300 px-2 py-1.5 text-sm hover:bg-gray-100"
          >
            <Search className="h-4 w-4" />
          </button>
          <button
            onClick={() => setHelpOpen(true)}
            title="키보드 단축키 (?)"
            className="inline-flex items-center gap-1 rounded border border-gray-300 px-2 py-1.5 text-sm hover:bg-gray-100"
          >
            <HelpCircle className="h-4 w-4" />
          </button>
          <span className="mx-1 h-5 w-px bg-gray-300" />
          {runStatus === "running" || runStatus === "queued" ? (
            <button
              onClick={() => runner.cancel()}
              title="실행 취소"
              className="inline-flex items-center gap-1 rounded border border-red-300 bg-red-50 px-2 py-1.5 text-sm text-red-700 hover:bg-red-100"
            >
              <StopCircle className="h-4 w-4" /> 취소
            </button>
          ) : (
            <button
              onClick={handleRun}
              title="실행 (Run)"
              className="inline-flex items-center gap-1 rounded border border-emerald-300 bg-emerald-50 px-2 py-1.5 text-sm text-emerald-800 hover:bg-emerald-100"
            >
              <Play className="h-4 w-4" /> 실행
            </button>
          )}
          <RunStatusIndicator />
          <span className="mx-1 h-5 w-px bg-gray-300" />
          <SaveStatusBadge status={saveStatus} dirty={dirty} />
          <button
            onClick={handleSave}
            disabled={saver.isPending || !dirty}
            className="inline-flex items-center gap-1 rounded bg-primary-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-primary-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            <Save className="h-4 w-4" /> 저장
          </button>
          <button
            onClick={handleCancel}
            className="inline-flex items-center gap-1 rounded border border-gray-300 px-3 py-1.5 text-sm hover:bg-gray-100"
          >
            <X className="h-4 w-4" /> 닫기
          </button>
        </div>
      </div>

      {/* Canvas + Parameter Panel + Execution Panel */}
      <div className="flex flex-1 flex-col overflow-hidden">
        <div className="flex flex-1 overflow-hidden">
          <div className="relative flex-1 overflow-hidden">
            <ScenarioCanvas
              nodes={nodes}
              edges={edges}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              onCommit={pushSnapshot}
            />
            <VariableExplorer nodes={nodes} />
          </div>
          <aside className="w-80 flex-shrink-0 border-l border-gray-200 bg-white">
            <ParameterPanel
              nodes={nodes}
              setNodes={setNodes}
              onCommit={pushSnapshot}
            />
          </aside>
        </div>
        <ExecutionPanel nodes={nodes} />
      </div>

      {/* Search palette */}
      <NodeSearchPalette
        open={searchOpen}
        onClose={() => setSearchOpen(false)}
        nodes={nodes}
        setNodes={setNodes}
        actions={actions}
        pushSnapshot={pushSnapshot}
      />

      {/* Keyboard shortcuts help */}
      <KeyboardShortcutsHelp
        open={helpOpen}
        onClose={() => setHelpOpen(false)}
      />

      {/* YAML preview */}
      <YamlPreviewModal
        open={yamlModalOpen}
        onClose={() => setYamlModalOpen(false)}
        workflow={yamlModalOpen ? buildMergedWorkflow() : null}
      />

      {/* Discard confirm modal */}
      {confirmCancel && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="rounded-lg bg-white p-6 shadow-xl">
            <div className="text-base font-semibold text-gray-900">
              저장되지 않은 변경사항이 있습니다
            </div>
            <div className="mt-1 text-sm text-gray-600">
              나가시면 변경사항이 사라집니다. 계속하시겠습니까?
            </div>
            <div className="mt-4 flex justify-end gap-2">
              <button
                onClick={() => setConfirmCancel(false)}
                className="rounded border border-gray-300 px-3 py-1.5 text-sm hover:bg-gray-100"
              >
                취소
              </button>
              <button
                onClick={handleConfirmDiscard}
                className="rounded bg-red-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-red-700"
              >
                나가기 (변경사항 버리기)
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function SaveStatusBadge({
  status,
  dirty,
}: {
  status: ReturnType<typeof useEditorStore.getState>["saveStatus"];
  dirty: boolean;
}) {
  if (status.kind === "saving") {
    return <span className="text-xs text-primary-600">저장 중...</span>;
  }
  if (status.kind === "error") {
    return (
      <span className="text-xs text-red-600" title={status.message}>
        ❗ 저장 실패
      </span>
    );
  }
  if (status.kind === "saved") {
    const time = new Date(status.at).toLocaleTimeString("ko-KR", {
      hour: "2-digit",
      minute: "2-digit",
    });
    return <span className="text-xs text-green-600">✓ 저장됨 {time}</span>;
  }
  return dirty ? (
    <span className="text-xs text-orange-600">● 변경사항 있음</span>
  ) : (
    <span className="text-xs text-gray-500">변경 없음</span>
  );
}
