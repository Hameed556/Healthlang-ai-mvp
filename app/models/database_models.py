"""
Database Models

SQLAlchemy ORM models for database tables.
"""

from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    DateTime,
    Text,
    JSON,
    ForeignKey,
    Index,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import func
# from datetime import datetime
import uuid

Base = declarative_base()


def generate_uuid():
    """Generate a UUID string."""
    return str(uuid.uuid4())


class User(Base):
    """User model."""
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=True)
    preferred_language = Column(String(10), default="en", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    queries = relationship(
        "Query", back_populates="user", cascade="all, delete-orphan"
    )
    translations = relationship(
        "Translation", back_populates="user", cascade="all, delete-orphan"
    )
    
    # Indexes
    __table_args__ = (
        Index('idx_users_email', 'email'),
        Index('idx_users_username', 'username'),
        Index('idx_users_created_at', 'created_at'),
    )


class Query(Base):
    """Medical query model."""
    __tablename__ = "queries"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(
        String(36), ForeignKey("users.id"), nullable=True, index=True
    )
    
    # Query fields
    query_text = Column(Text, nullable=False)
    query_type = Column(String(50), nullable=True)
    language = Column(String(10), default="en", nullable=False)
    
    # Response fields (supporting both old and new formats)
    # Old format - structured medical analysis
    analysis = Column(Text, nullable=True)
    # New format - direct response text
    response_text = Column(Text, nullable=True)
    
    # Medical analysis fields
    recommendations = Column(JSON, nullable=True)
    safety_level = Column(String(20), nullable=True)
    confidence_score = Column(Float, nullable=True)
    disclaimers = Column(JSON, nullable=True)
    follow_up_questions = Column(JSON, nullable=True)
    emergency_indicators = Column(JSON, nullable=True)
    
    # Source and metadata
    sources = Column(Text, nullable=True)  # Comma-separated URLs or JSON
    processing_time = Column(Float, nullable=False)
    request_metadata = Column(JSON, nullable=True)
    
    # Status fields
    success = Column(Boolean, default=True, nullable=False)
    error = Column(Text, nullable=True)
    original_language = Column(String(10), default="en", nullable=False)
    target_language = Column(String(10), default="en", nullable=False)
    
    # Timestamp
    timestamp = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    
    # Relationships
    user = relationship("User", back_populates="queries")
    
    # Indexes
    __table_args__ = (
        Index('idx_queries_user_id', 'user_id'),
        Index('idx_queries_created_at', 'created_at'),
        Index('idx_queries_timestamp', 'timestamp'),
        Index('idx_queries_language', 'language'),
        Index('idx_queries_query_type', 'query_type'),
        Index('idx_queries_safety_level', 'safety_level'),
        Index('idx_queries_success', 'success'),
    )


class Translation(Base):
    """Translation model (deprecated; kept for compatibility)."""
    __tablename__ = "translations"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(
        String(36), ForeignKey("users.id"), nullable=True, index=True
    )
    original_text = Column(Text, nullable=True)
    translated_text = Column(Text, nullable=True)
    source_language = Column(String(10), nullable=True)
    target_language = Column(String(10), nullable=True)
    confidence_score = Column(Float, nullable=True)
    processing_time = Column(Float, nullable=True)
    context = Column(Text, nullable=True)
    preserve_formatting = Column(Boolean, default=True, nullable=False)
    request_metadata = Column(JSON, nullable=True)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    
    # Relationships
    user = relationship("User", back_populates="translations")
    
    # Indexes
    __table_args__ = (
        Index('idx_translations_user_id', 'user_id'),
        Index('idx_translations_created_at', 'created_at'),
        Index('idx_translations_source_language', 'source_language'),
        Index('idx_translations_target_language', 'target_language'),
    )


class Document(Base):
    """Document model for RAG system."""
    __tablename__ = "documents"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    title = Column(String(255), nullable=True)
    content = Column(Text, nullable=False)
    content_type = Column(String(50), nullable=False)  # pdf, docx, txt, etc.
    source_url = Column(String(500), nullable=True)
    source_file = Column(String(255), nullable=True)
    language = Column(String(10), default="en", nullable=False)
    document_metadata = Column(JSON, nullable=True)
    embedding_model = Column(String(100), nullable=True)
    vector_id = Column(String(255), nullable=True)  # ID in vector store
    is_processed = Column(Boolean, default=False, nullable=False)
    is_indexed = Column(Boolean, default=False, nullable=False)
    processing_time = Column(Float, nullable=True)
    file_size = Column(Integer, nullable=True)
    checksum = Column(String(64), nullable=True)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    
    # Indexes
    __table_args__ = (
        Index('idx_documents_content_type', 'content_type'),
        Index('idx_documents_language', 'language'),
        Index('idx_documents_is_processed', 'is_processed'),
        Index('idx_documents_is_indexed', 'is_indexed'),
        Index('idx_documents_created_at', 'created_at'),
    )


class DocumentChunk(Base):
    """Document chunk model for RAG system."""
    __tablename__ = "document_chunks"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    document_id = Column(
        String(36), ForeignKey("documents.id"), nullable=False, index=True
    )
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    embedding = Column(JSON, nullable=True)  # Store embedding as JSON array
    chunk_metadata = Column(JSON, nullable=True)
    vector_id = Column(String(255), nullable=True)  # ID in vector store
    similarity_score = Column(Float, nullable=True)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    
    # Relationships
    document = relationship("Document")
    
    # Indexes
    __table_args__ = (
        Index('idx_document_chunks_document_id', 'document_id'),
        Index('idx_document_chunks_chunk_index', 'chunk_index'),
        Index('idx_document_chunks_vector_id', 'vector_id'),
    )


class Collection(Base):
    """Collection model for organizing documents."""
    __tablename__ = "collections"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    collection_metadata = Column(JSON, nullable=True)
    document_count = Column(Integer, default=0, nullable=False)
    embedding_model = Column(String(100), nullable=True)
    vector_store_type = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    
    # Indexes
    __table_args__ = (
        Index('idx_collections_name', 'name'),
        Index('idx_collections_is_active', 'is_active'),
    )


class CollectionDocument(Base):
    """Many-to-many relationship between collections and documents."""
    __tablename__ = "collection_documents"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    collection_id = Column(
        String(36), ForeignKey("collections.id"), nullable=False, index=True
    )
    document_id = Column(
        String(36), ForeignKey("documents.id"), nullable=False, index=True
    )
    added_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    
    # Indexes
    __table_args__ = (
        Index('idx_collection_documents_collection_id', 'collection_id'),
        Index('idx_collection_documents_document_id', 'document_id'),
        Index(
            'idx_collection_documents_unique',
            'collection_id',
            'document_id',
            unique=True,
        ),
    )


class APIKey(Base):
    """API key model for external integrations."""
    __tablename__ = "api_keys"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(
        String(36), ForeignKey("users.id"), nullable=False, index=True
    )
    name = Column(String(100), nullable=False)
    key_hash = Column(String(255), nullable=False)
    permissions = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    last_used = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    
    # Indexes
    __table_args__ = (
        Index('idx_api_keys_user_id', 'user_id'),
        Index('idx_api_keys_key_hash', 'key_hash'),
        Index('idx_api_keys_is_active', 'is_active'),
    )


class AuditLog(Base):
    """Audit log model for tracking system activities."""
    __tablename__ = "audit_logs"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(
        String(36), ForeignKey("users.id"), nullable=True, index=True
    )
    action = Column(String(100), nullable=False)
    resource_type = Column(String(50), nullable=False)
    resource_id = Column(String(36), nullable=True)
    details = Column(JSON, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    
    # Indexes
    __table_args__ = (
        Index('idx_audit_logs_user_id', 'user_id'),
        Index('idx_audit_logs_action', 'action'),
        Index('idx_audit_logs_resource_type', 'resource_type'),
        Index('idx_audit_logs_created_at', 'created_at'),
    )


class SystemMetric(Base):
    """System metrics model for monitoring."""
    __tablename__ = "system_metrics"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    metric_name = Column(String(100), nullable=False, index=True)
    metric_value = Column(Float, nullable=False)
    metric_unit = Column(String(20), nullable=True)
    labels = Column(JSON, nullable=True)
    timestamp = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    
    # Indexes
    __table_args__ = (
        Index('idx_system_metrics_name', 'metric_name'),
        Index('idx_system_metrics_timestamp', 'timestamp'),
    )


class RateLimit(Base):
    """Rate limiting model."""
    __tablename__ = "rate_limits"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    # key can be IP, user_id, or API key
    key = Column(String(255), nullable=False, index=True)
    endpoint = Column(String(100), nullable=False)
    window_start = Column(DateTime(timezone=True), nullable=False)
    request_count = Column(Integer, default=0, nullable=False)
    limit = Column(Integer, nullable=False)
    window_size = Column(Integer, nullable=False)  # in seconds
    
    # Indexes
    __table_args__ = (
        Index('idx_rate_limits_key', 'key'),
        Index('idx_rate_limits_endpoint', 'endpoint'),
        Index('idx_rate_limits_window_start', 'window_start'),
    )


# ---------------------
# Conversational Memory
# ---------------------

class Conversation(Base):
    """A conversation thread owned by a user (similar to ChatGPT chats)."""
    __tablename__ = "conversations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(
        String(36), ForeignKey("users.id"), nullable=False, index=True
    )
    title = Column(String(200), nullable=True)
    archived = Column(Boolean, default=False, nullable=False)
    conversation_metadata = Column(JSON, nullable=True)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    __table_args__ = (
        Index('idx_conversations_user_id', 'user_id'),
        Index('idx_conversations_archived', 'archived'),
        Index('idx_conversations_updated_at', 'updated_at'),
    )


class Message(Base):
    """A single chat message within a conversation."""
    __tablename__ = "messages"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    conversation_id = Column(
        String(36), ForeignKey("conversations.id"), nullable=False, index=True
    )
    user_id = Column(
        String(36), ForeignKey("users.id"), nullable=True, index=True
    )
    # role values: user | assistant | system | tool
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    model = Column(String(100), nullable=True)
    tokens = Column(Integer, nullable=True)
    latency = Column(Float, nullable=True)
    tool_calls = Column(JSON, nullable=True)
    attachments = Column(JSON, nullable=True)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        Index('idx_messages_conversation_id', 'conversation_id'),
        Index('idx_messages_user_id', 'user_id'),
        Index('idx_messages_role', 'role'),
        Index('idx_messages_created_at', 'created_at'),
    )


class ConversationSummary(Base):
    """Rolling summary to preserve long-term memory with low token use."""
    __tablename__ = "conversation_summaries"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    conversation_id = Column(
        String(36), ForeignKey("conversations.id"), nullable=False, index=True
    )
    summary_text = Column(Text, nullable=False)
    token_count = Column(Integer, nullable=True)
    last_message_id = Column(String(36), nullable=True)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        Index('idx_conversation_summaries_conversation_id', 'conversation_id'),
        Index('idx_conversation_summaries_updated_at', 'updated_at'),
    )


class UserPreference(Base):
    """Per-user settings and feature flags (for front-end sync)."""
    __tablename__ = "user_preferences"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(
        String(36), ForeignKey("users.id"), nullable=False, index=True
    )
    # e.g., theme, default_language, safe_mode
    preferences = Column(JSON, nullable=True)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    __table_args__ = (
        Index('idx_user_preferences_user_id', 'user_id'),
    )
