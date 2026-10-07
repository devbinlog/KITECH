"""Query route - Main NL query endpoint"""

import logging
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator

from ...nl_router_agent import get_nl_router
from ...context import get_conversation_manager

logger = logging.getLogger(__name__)

router = APIRouter()

_DEPRECATION_HEADERS = {
    "Deprecation": "true",
    "Link": '<http://agent-orchestrator:8020/api/v1/chat>; rel="successor-version"',
}


class QueryRequest(BaseModel):
    """Natural language query request"""

    query: str = Field(..., min_length=1, max_length=500, description="Natural language query")
    session_id: Optional[str] = Field(None, description="Session ID for conversation context")
    user_id: Optional[str] = Field(None, description="User ID for context association")

    @field_validator("query")
    @classmethod
    def strip_and_validate(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("Query must contain non-whitespace characters")
        return v


class QueryResponse(BaseModel):
    """Query response with UI schema"""

    success: bool
    intent: str
    entities: Dict[str, Any] = Field(default_factory=dict)
    data: Dict[str, Any] = Field(default_factory=dict)
    ui_schema: Optional[Dict[str, Any]] = None
    text_response: str = ""
    errors: list = Field(default_factory=list)


@router.post("/query", response_model=QueryResponse)
async def process_query(
    request: QueryRequest,
    authorization: Optional[str] = Header(None),
    x_session_id: Optional[str] = Header(None),
) -> JSONResponse:
    """
    [DEPRECATED — use agent-orchestrator]
    Migrate to: POST http://agent-orchestrator:8020/api/v1/chat

    Process a natural language query

    This endpoint:
    1. Classifies the intent of the query
    2. Extracts relevant entities (with context for implicit references)
    3. Selects appropriate skills
    4. Executes API calls
    5. Generates UI schema for rendering
    6. Maintains conversation context

    Session ID can be provided via:
    - request.session_id in body
    - X-Session-ID header

    Examples:
    - "오늘 생산 현황 보여줘"
    - "CNC-001 설비 상태 어때?"
    - "그 설비 가동률은?" (uses previous equipment from context)
    - "어제 생산량 비교해줘"
    """
    logger.warning(
        "DEPRECATED: POST /query — migrate to agent-orchestrator POST /api/v1/chat"
    )
    nl_router = get_nl_router()

    # Extract token from Authorization header
    auth_token = None
    if authorization and authorization.startswith("Bearer "):
        auth_token = authorization[7:]

    # Use session_id from request body or header
    session_id = request.session_id or x_session_id

    # Process query with session context
    result = await nl_router.process_query(
        query=request.query,
        session_id=session_id,
        user_id=request.user_id,
        auth_token=auth_token,
    )

    body = QueryResponse(
        success=result.success,
        intent=result.intent.value,
        entities=result.entities,
        data=result.data,
        ui_schema=result.ui_schema,
        text_response=result.text_response,
        errors=result.errors,
    )
    return JSONResponse(content=body.model_dump(), headers=_DEPRECATION_HEADERS)


class DebugQueryResponse(QueryResponse):
    """Query response with debug info"""

    debug_info: Dict[str, Any] = Field(default_factory=dict)


@router.post("/query/debug", response_model=DebugQueryResponse)
async def process_query_debug(
    request: QueryRequest,
    authorization: Optional[str] = Header(None),
    x_session_id: Optional[str] = Header(None),
) -> JSONResponse:
    """
    [DEPRECATED — use agent-orchestrator]
    Migrate to: POST http://agent-orchestrator:8020/api/v1/chat

    Process query with debug information

    Same as /query but includes debug info about:
    - Intent classification details
    - Entity extraction results
    - Skill matching
    - API call plan
    - Session context
    """
    logger.warning(
        "DEPRECATED: POST /query/debug — migrate to agent-orchestrator POST /api/v1/chat"
    )
    nl_router = get_nl_router()

    auth_token = None
    if authorization and authorization.startswith("Bearer "):
        auth_token = authorization[7:]

    session_id = request.session_id or x_session_id

    result = await nl_router.process_query(
        query=request.query,
        session_id=session_id,
        user_id=request.user_id,
        auth_token=auth_token,
    )

    body = DebugQueryResponse(
        success=result.success,
        intent=result.intent.value,
        entities=result.entities,
        data=result.data,
        ui_schema=result.ui_schema,
        text_response=result.text_response,
        errors=result.errors,
        debug_info=result.debug_info,
    )
    return JSONResponse(content=body.model_dump(), headers=_DEPRECATION_HEADERS)


class IntentRequest(BaseModel):
    """Intent classification request"""

    query: str = Field(..., min_length=1, max_length=500)


class IntentResponse(BaseModel):
    """Intent classification response"""

    intent: str
    confidence: float
    entities: Dict[str, Any]
    requires_clarification: bool
    suggested_questions: list


@router.post("/classify", response_model=IntentResponse)
async def classify_intent(request: IntentRequest) -> IntentResponse:
    """
    Classify intent without executing APIs

    Useful for testing intent classification.
    """
    nl_router = get_nl_router()

    intent_result = await nl_router.intent_classifier.classify(request.query)

    return IntentResponse(
        intent=intent_result.intent.value,
        confidence=intent_result.confidence,
        entities=intent_result.entities,
        requires_clarification=intent_result.requires_clarification,
        suggested_questions=intent_result.suggested_questions,
    )


# Conversation history endpoints


class ConversationHistoryResponse(BaseModel):
    """Conversation history response"""

    session_id: str
    messages: List[Dict[str, Any]]
    active_entities: Dict[str, Any]


@router.get("/conversation/{session_id}/history", response_model=ConversationHistoryResponse)
async def get_conversation_history(
    session_id: str,
    limit: int = 50,
) -> ConversationHistoryResponse:
    """
    [DEPRECATED — use agent-orchestrator]
    Conversation history is now owned by agent-orchestrator (SqliteSaver).
    This endpoint returns data from nl-router's local in-memory store only.

    Get conversation history for a session

    Returns recent messages and active entities.
    """
    logger.warning(
        "DEPRECATED: GET /conversation/%s/history — "
        "history is owned by agent-orchestrator SqliteSaver",
        session_id,
    )
    manager = get_conversation_manager()

    if session_id not in manager._contexts:
        raise HTTPException(status_code=404, detail="Session not found")

    context = manager._contexts[session_id]
    messages = manager.get_history(session_id, limit)

    return ConversationHistoryResponse(
        session_id=session_id,
        messages=messages,
        active_entities=context.active_entities,
    )


@router.delete("/conversation/{session_id}")
async def clear_conversation(session_id: str) -> Dict[str, str]:
    """
    [DEPRECATED — use agent-orchestrator]
    Conversation state is now owned by agent-orchestrator (SqliteSaver).

    Clear conversation context for a session
    """
    logger.warning(
        "DEPRECATED: DELETE /conversation/%s — "
        "conversation state is owned by agent-orchestrator",
        session_id,
    )
    manager = get_conversation_manager()
    manager.clear_context(session_id)

    return {"message": f"Conversation {session_id} cleared"}
