from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.chat.chat_service import ChatService
from app.api.routes.auth import get_current_user
from app.core.workflow import HealthLangWorkflow
from app.utils.logger import get_logger

router = APIRouter(prefix="/chat", tags=["chat"])
logger = get_logger(__name__)

def get_workflow(request: Request) -> HealthLangWorkflow:
    """Dependency to get the initialized workflow from app state"""
    workflow = getattr(request.app.state, 'workflow', None)
    logger.info(f"get_workflow called: workflow is {'SET' if workflow else 'NOT SET'}")
    if workflow:
        logger.info(f"Workflow _general_knowledge_rag: {'SET' if workflow._general_knowledge_rag else 'NOT SET'}")
    return workflow


@router.post("/conversations", summary="Create a new conversation")
def create_conversation(
    title: Optional[str] = None,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
    workflow: HealthLangWorkflow = Depends(get_workflow),
):
    service = ChatService(workflow=workflow)
    conv = service.create_conversation(db, user_id=user.id, title=title)
    return {"conversation_id": conv.id, "title": conv.title}


@router.get("/conversations", summary="List conversations")
def list_conversations(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
    workflow: HealthLangWorkflow = Depends(get_workflow),
):
    service = ChatService(workflow=workflow)
    rows = service.list_conversations(
        db, user_id=user.id, limit=limit, offset=offset
    )
    return [
        {
            "id": c.id,
            "title": c.title,
            "archived": c.archived,
            "created_at": c.created_at,
            "updated_at": c.updated_at,
        }
        for c in rows
    ]


@router.patch(
    "/conversations/{conversation_id}",
    summary="Rename or archive conversation",
)
def update_conversation(
    conversation_id: str,
    title: Optional[str] = None,
    archived: Optional[bool] = None,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
    workflow: HealthLangWorkflow = Depends(get_workflow),
):
    service = ChatService(workflow=workflow)
    conv = None
    if title is not None:
        conv = service.rename_conversation(db, conversation_id, user.id, title)
    if archived is not None:
        conv = service.archive_conversation(
            db, conversation_id, user.id, archived
        )
    if not conv:
        raise HTTPException(status_code=400, detail="No updates provided")
    return {"id": conv.id, "title": conv.title, "archived": conv.archived}


@router.delete("/conversations/{conversation_id}", status_code=204)
def delete_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
    workflow: HealthLangWorkflow = Depends(get_workflow),
):
    service = ChatService(workflow=workflow)
    service.delete_conversation(db, conversation_id, user.id)
    return {"status": "deleted"}


@router.get(
    "/conversations/{conversation_id}/messages",
    summary="Get messages",
)
def get_messages(
    conversation_id: str,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
    workflow: HealthLangWorkflow = Depends(get_workflow),
):
    service = ChatService(workflow=workflow)
    rows = service.get_messages(db, conversation_id, user.id, limit, offset)
    return [
        {
            "id": m.id,
            "role": m.role,
            "content": m.content,
            "created_at": m.created_at,
        }
        for m in rows
    ]


@router.post(
    "/conversations/{conversation_id}/messages",
    summary="Send a message and get reply",
)
async def send_message(
    conversation_id: str,
    text: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
    workflow: HealthLangWorkflow = Depends(get_workflow),
):
    service = ChatService(workflow=workflow)
    reply = await service.send_and_generate(db, conversation_id, user.id, text)
    return {
        "message": {
            "id": reply.id,
            "role": reply.role,
            "content": reply.content,
            "created_at": reply.created_at,
        }
    }


@router.post(
    "/conversations/{conversation_id}/messages/stream",
    summary="Send a message and stream the AI response (SSE)",
)
async def send_message_stream(
    conversation_id: str,
    text: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
    workflow: HealthLangWorkflow = Depends(get_workflow),
):
    """Stream AI response using Server-Sent Events (SSE)"""
    service = ChatService(workflow=workflow)
    
    async def event_generator():
        async for event in service.send_and_generate_stream(db, conversation_id, user.id, text):
            yield event
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
