"use client";

/**
 * RoutingEdge — bezier connection with optional `when` label.
 *
 * Renders a default React Flow bezier path; if the edge data carries a
 * `when` expression (set by useScenarioLoader from step.routing[i].when),
 * draw a small pill near the source.
 *
 * Design Ref: §5.4 Edges checklist (When 표현식 라벨)
 */

import {
  BaseEdge,
  EdgeLabelRenderer,
  getBezierPath,
  type EdgeProps,
} from "reactflow";

interface RoutingEdgeData {
  when?: string | null;
}

export function RoutingEdge(props: EdgeProps<RoutingEdgeData>) {
  const {
    id,
    sourceX,
    sourceY,
    targetX,
    targetY,
    sourcePosition,
    targetPosition,
    style,
    markerEnd,
    data,
  } = props;

  const [path, labelX, labelY] = getBezierPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
  });

  const label = (data?.when ?? "").trim();
  const truncated = label.length > 28 ? `${label.slice(0, 25)}…` : label;

  return (
    <>
      <BaseEdge id={id} path={path} markerEnd={markerEnd} style={style} />
      {truncated && (
        <EdgeLabelRenderer>
          <div
            style={{
              position: "absolute",
              transform: `translate(-50%, -50%) translate(${labelX}px,${labelY}px)`,
              pointerEvents: "all",
            }}
            className="rounded-full border border-gray-200 bg-white px-2 py-0.5 font-mono text-[10px] text-gray-700 shadow-sm"
            title={label}
          >
            {truncated}
          </div>
        </EdgeLabelRenderer>
      )}
    </>
  );
}
