from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select, desc
from app.models.database_models import (
    Conversation,
    Message,
    ConversationSummary,
)
from app.core.workflow import HealthLangWorkflow
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ChatService:
    """Encapsulates conversation/message operations and generation."""

    def __init__(self, workflow: Optional[HealthLangWorkflow] = None):
        self.workflow = workflow or HealthLangWorkflow()

    # ---- Conversations ----
    def create_conversation(
        self, db: Session, user_id: str, title: Optional[str] = None
    ) -> Conversation:
        conv = Conversation(user_id=user_id, title=title)
        db.add(conv)
        db.commit()
        db.refresh(conv)
        return conv

    def list_conversations(
        self, db: Session, user_id: str, limit: int = 50, offset: int = 0
    ) -> List[Conversation]:
        stmt = (
            select(Conversation)
            .where(
                Conversation.user_id == user_id,
                Conversation.archived == False,  # noqa: E712
            )
            .order_by(desc(Conversation.updated_at))
            .limit(limit)
            .offset(offset)
        )
        return list(db.execute(stmt).scalars())

    def rename_conversation(
        self, db: Session, conversation_id: str, user_id: str, title: str
    ) -> Conversation:
        conv = db.get(Conversation, conversation_id)
        if not conv or conv.user_id != user_id:
            raise PermissionError("Conversation not found or access denied")
        conv.title = title
        db.commit()
        db.refresh(conv)
        return conv

    def archive_conversation(
        self,
        db: Session,
        conversation_id: str,
        user_id: str,
        archived: bool = True,
    ) -> Conversation:
        conv = db.get(Conversation, conversation_id)
        if not conv or conv.user_id != user_id:
            raise PermissionError("Conversation not found or access denied")
        conv.archived = archived
        db.commit()
        db.refresh(conv)
        return conv

    def delete_conversation(
        self, db: Session, conversation_id: str, user_id: str
    ) -> None:
        conv = db.get(Conversation, conversation_id)
        if not conv or conv.user_id != user_id:
            raise PermissionError("Conversation not found or access denied")
        db.delete(conv)
        db.commit()

    # ---- Messages ----
    def get_messages(
        self,
        db: Session,
        conversation_id: str,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Message]:
        conv = db.get(Conversation, conversation_id)
        if not conv or conv.user_id != user_id:
            raise PermissionError("Conversation not found or access denied")
        stmt = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at)
            .limit(limit)
            .offset(offset)
        )
        return list(db.execute(stmt).scalars())

    def _build_context(
        self, db: Session, conversation_id: str, max_messages: int = 12
    ) -> Tuple[List[dict], Optional[str]]:
        """Return the last N messages and optional summary prompt."""
        # Pull rolling summary if any
        summary_stmt = select(ConversationSummary).where(
            ConversationSummary.conversation_id == conversation_id
        )
        summary = db.execute(summary_stmt).scalars().first()
        summary_text = summary.summary_text if summary else None

        # Pull tail messages
        stmt = select(Message).where(
            Message.conversation_id == conversation_id
        ).order_by(desc(Message.created_at)).limit(max_messages)
        rows = list(db.execute(stmt).scalars())[::-1]
        history = [{"role": m.role, "content": m.content} for m in rows]
        return history, summary_text

    def _maybe_update_summary(
        self, db: Session, conversation_id: str, messages_tail: List[dict]
    ) -> None:
        """Very simple heuristic: summarize every ~20 messages via workflow."""
        try:
            count_stmt = select(Message).where(
                Message.conversation_id == conversation_id
            )
            total = db.execute(count_stmt).scalars().all()
            if len(total) % 20 != 0:
                return
            # Generate a compact summary using the workflow LLM
            text = "\n".join(
                [f"{m['role']}: {m['content']}" for m in messages_tail[-10:]]
            )
            prompt = (
                "Summarize the key facts, decisions, and user "
                "preferences from this chat "
                "in 6-10 bullet points. Keep it under 800 tokens.\n\n" + text
            )
            # Minimal summarization: store the recent window as-is.
            # You can replace this with a proper LLM summarizer later.
            summary = prompt[:4000]
            # Upsert summary
            stmt = select(ConversationSummary).where(
                ConversationSummary.conversation_id == conversation_id
            )
            existing = db.execute(stmt).scalars().first()
            if existing:
                existing.summary_text = summary
            else:
                db.add(
                    ConversationSummary(
                        conversation_id=conversation_id,
                        summary_text=summary,
                    )
                )
            db.commit()
        except Exception as e:
            logger.warning(f"Failed to update summary: {e}")

    async def send_and_generate(
        self, db: Session, conversation_id: str, user_id: str, user_text: str
    ) -> Message:
        conv = db.get(Conversation, conversation_id)
        if not conv or conv.user_id != user_id:
            raise PermissionError("Conversation not found or access denied")

        # Save user message
        user_msg = Message(
            conversation_id=conversation_id,
            user_id=user_id,
            role="user",
            content=user_text,
        )
        db.add(user_msg)
        db.commit()
        db.refresh(user_msg)

        # Build context from history + (optional) summary
        history, summary_text = self._build_context(db, conversation_id)

        # Ask the workflow
        # Compose a prompt that includes compact context for medical Q&A
        context_lines = []
        if summary_text:
            context_lines.append("Conversation summary:\n" + summary_text)
        if history:
            context_lines.append("Recent messages:")
            for m in history[-10:]:
                context_lines.append(f"- {m['role']}: {m['content']}")
        context_lines.append(f"User: {user_text}")
        context_lines.append(
            "Assistant: Provide a concise, medically safe, markdown-formatted "
            "answer. Include sources if used."
        )
        composed = "\n".join(context_lines)

        result = await self.workflow.process_query(composed, original_query=user_text)
        reply_text = result.get("response") or "(No response)"

        # Save assistant message
        assistant_msg = Message(
            conversation_id=conversation_id,
            role="assistant",
            content=reply_text,
        )
        db.add(assistant_msg)
        conv.updated_at = conv.updated_at  # touch handled by onupdate
        db.commit()
        db.refresh(assistant_msg)

        # Maybe update summary occasionally
        self._maybe_update_summary(
            db,
            conversation_id,
            history
            + [
                {"role": "user", "content": user_text},
                {"role": "assistant", "content": reply_text},
            ],
        )

        return assistant_msg

    async def send_and_generate_stream(self, db: Session, conversation_id: str, user_id: str, user_text: str):
        """Stream AI response and save messages afterward"""
        conv = db.get(Conversation, conversation_id)
        if not conv or conv.user_id != user_id:
            raise PermissionError("Conversation not found or access denied")

        # Save user message
        user_msg = Message(
            conversation_id=conversation_id,
            user_id=user_id,
            role="user",
            content=user_text,
        )
        db.add(user_msg)
        db.commit()
        db.refresh(user_msg)

        # Build context from history + (optional) summary
        history, summary_text = self._build_context(db, conversation_id)

        # Compose prompt with context
        context_lines = []
        if summary_text:
            context_lines.append("Conversation summary:\n" + summary_text)
        if history:
            context_lines.append("Recent messages:")
            for m in history[-10:]:
                context_lines.append(f"- {m['role']}: {m['content']}")
        context_lines.append(f"User: {user_text}")
        context_lines.append(
            "Assistant: Provide a concise, medically safe, markdown-formatted "
            "answer. Include sources if used."
        )
        composed = "\n".join(context_lines)

        # Stream the response
        full_response = ""
        async for event in self.workflow.process_query_stream(composed, original_query=user_text):
            yield event
            # Parse event to collect response text
            try:
                import json
                event_data = json.loads(event.strip())
                if event_data.get("event") == "content":
                    full_response += event_data.get("data", "")
            except (json.JSONDecodeError, ValueError, KeyError):
                pass

        # Save assistant message
        if not full_response:
            full_response = "(No response)"
        
        assistant_msg = Message(
            conversation_id=conversation_id,
            role="assistant",
            content=full_response,
        )
        db.add(assistant_msg)
        conv.updated_at = conv.updated_at  # touch handled by onupdate
        db.commit()
        db.refresh(assistant_msg)

        # Maybe update summary
        self._maybe_update_summary(
            db,
            conversation_id,
            history + [
                {"role": "user", "content": user_text},
                {"role": "assistant", "content": full_response},
            ],
        )
