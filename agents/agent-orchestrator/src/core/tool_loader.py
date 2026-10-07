"""core/tool_loader.py — Service registry → LangChain tools.

Reads the internal-services registry YAML, discovers each service's
/capabilities endpoint, and builds StructuredTool instances that POST to
the appropriate endpoint with proper auth + trace-id propagation.
"""
from __future__ import annotations

import asyncio
import logging
import os
from typing import Any, Dict, List, Optional

import httpx
import yaml
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, create_model

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Capability fetching
# ---------------------------------------------------------------------------


async def fetch_capabilities(
    client: httpx.AsyncClient,
    base_url: str,
) -> Optional[Dict[str, Any]]:
    """Best-effort GET /capabilities for a service. Returns None on failure."""
    try:
        r = await client.get(f"{base_url}/capabilities", timeout=5.0)
        r.raise_for_status()
        return r.json()
    except Exception as exc:
        logger.warning("capabilities fetch failed for %s: %s", base_url, exc)
        return None


# ---------------------------------------------------------------------------
# Tool factory
# ---------------------------------------------------------------------------


def _make_tool(
    service_name: str,
    base_url: str,
    tool_meta: Dict[str, Any],
    internal_key: str,
) -> StructuredTool:
    """Build a LangChain StructuredTool that POSTs/GETs to <base_url><endpoint>."""
    name = f"{service_name}__{tool_meta['name']}"
    description = tool_meta.get("description", "")
    endpoint = tool_meta.get("endpoint", {})
    method = endpoint.get("method", "POST").upper()
    path = endpoint.get("path", "/")

    # Generic free-form input schema
    InputModel: type[BaseModel] = create_model(
        f"{name}_Input",
        payload=(Dict[str, Any], ...),
    )

    async def _call(payload: Dict[str, Any]) -> Any:
        from shared.common.tracing import get_trace_id

        # Send BOTH header names: shared/common library agents accept "X-Internal-Key",
        # cell-mes accepts "X-Internal-Service-Key". Until headers are unified, dual-send.
        headers: Dict[str, str] = {
            "X-Internal-Key": internal_key,
            "X-Internal-Service-Key": internal_key,
        }
        tid = get_trace_id()
        if tid:
            headers["X-Trace-Id"] = tid
        async with httpx.AsyncClient(timeout=30.0) as c:
            r = await c.request(method, f"{base_url}{path}", json=payload, headers=headers)
            r.raise_for_status()
            return r.json()

    return StructuredTool.from_function(
        coroutine=_call,
        name=name,
        description=description,
        args_schema=InputModel,
    )


# ---------------------------------------------------------------------------
# Registry loader
# ---------------------------------------------------------------------------


async def load_tools_from_registry(
    yaml_path: Optional[str] = None,
    exclude: Optional[List[str]] = None,
) -> List[StructuredTool]:
    """Load all capability-equipped services from registry YAML and build tools.

    Args:
        yaml_path: Path to internal-services.yaml. Defaults to
            SERVICE_REGISTRY_PATH env var or /app/config/internal-services.yaml.
        exclude: Service names to skip (default: ["agent-orchestrator"]).

    Returns:
        List of StructuredTool instances ready for LangGraph agent binding.
    """
    yaml_path = yaml_path or os.getenv(
        "SERVICE_REGISTRY_PATH",
        "/app/config/internal-services.yaml",
    )
    excluded = set(exclude or ["agent-orchestrator"])
    internal_key = os.getenv("INTERNAL_SERVICE_KEY", "")

    with open(yaml_path) as f:
        registry = yaml.safe_load(f)

    services = [
        s
        for s in registry.get("services", [])
        if s.get("name") not in excluded and s.get("capabilities")
    ]

    tools: List[StructuredTool] = []

    async with httpx.AsyncClient() as client:
        results = await asyncio.gather(
            *(fetch_capabilities(client, s["base_url"]) for s in services)
        )

    for svc, caps in zip(services, results):
        if caps is None:
            continue
        for tool_meta in caps.get("tools", []):
            tools.append(_make_tool(svc["name"], svc["base_url"], tool_meta, internal_key))

    logger.info("loaded %d tools from %d services", len(tools), len(services))
    return tools
