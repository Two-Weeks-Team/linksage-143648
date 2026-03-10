import os
import re
from datetime import datetime
from typing import List
from uuid import uuid4

from dotenv import load_dotenv
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    String,
    Table,
    Text,
    create_engine,
    inspect,
    func,
    text,
    UUID,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
    sessionmaker,
)

# Load environment variables from .env if present
load_dotenv()

# ---------------------------------------------------------------------------
# Database URL handling with automatic scheme fixing and SSL config
# ---------------------------------------------------------------------------
_raw_url = os.getenv(
    "DATABASE_URL",
    os.getenv("POSTGRES_URL", "sqlite:///./app.db"),
)
# Fix common scheme issues
if _raw_url.startswith("postgresql+asyncpg://"):
    _raw_url = _raw_url.replace("postgresql+asyncpg://", "postgresql+psycopg://")
if _raw_url.startswith("postgres://"):
    _raw_url = _raw_url.replace("postgres://", "postgresql+psycopg://")

# Determine if we need SSL args (non‑localhost and not SQLite)
_use_ssl = False
if not _raw_url.startswith("sqlite") and "localhost" not in _raw_url and "127.0.0.1" not in _raw_url:
    _use_ssl = True

_connect_args = {"sslmode": "require"} if _use_ssl else {}

engine = create_engine(_raw_url, connect_args=_connect_args, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

# ---------------------------------------------------------------------------
# Table name prefix to avoid collisions in shared DBs
# ---------------------------------------------------------------------------
PREFIX = "ls_"

class Base(DeclarativeBase):
    pass

# Association table for many‑to‑many Bookmark <-> Tag
bookmark_tag = Table(
    f"{PREFIX}bookmark_tag",
    Base.metadata,
    Column("bookmark_id", UUID(as_uuid=True), ForeignKey(f"{PREFIX}bookmarks.id"), primary_key=True),
    Column("tag_id", UUID(as_uuid=True), ForeignKey(f"{PREFIX}tags.id"), primary_key=True),
    Column("confidence_score", Float, nullable=False, default=0.0),
    Column("is_primary", Boolean, nullable=False, default=False),
)

# ---------------------------------------------------------------------------
# SQLAlchemy models
# ---------------------------------------------------------------------------
class User(Base):
    __tablename__ = f"{PREFIX}users"

    id: Mapped[uuid4] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    is_premium: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    bookmarks = relationship("Bookmark", back_populates="owner")

class Bookmark(Base):
    __tablename__ = f"{PREFIX}bookmarks"

    id: Mapped[uuid4] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[uuid4] = mapped_column(UUID(as_uuid=True), ForeignKey(f"{PREFIX}users.id"), nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    is_private: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    owner = relationship("User", back_populates="bookmarks")
    summary = relationship("Summary", uselist=False, back_populates="bookmark")
    tags = relationship("Tag", secondary=bookmark_tag, back_populates="bookmarks")
    relationships = relationship("Relationship", foreign_keys="Relationship.source_id", back_populates="source")

class Summary(Base):
    __tablename__ = f"{PREFIX}summaries"

    id: Mapped[uuid4] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    bookmark_id: Mapped[uuid4] = mapped_column(UUID(as_uuid=True), ForeignKey(f"{PREFIX}bookmarks.id"), nullable=False, unique=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    is_edited: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    model_version: Mapped[str] = mapped_column(String(50), nullable=False, default="unknown")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    bookmark = relationship("Bookmark", back_populates="summary")

class Tag(Base):
    __tablename__ = f"{PREFIX}tags"

    id: Mapped[uuid4] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    type: Mapped[str] = mapped_column(String(20), nullable=False)  # 'ai_generated' or 'user_defined'
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    bookmarks = relationship("Bookmark", secondary=bookmark_tag, back_populates="tags")

class Relationship(Base):
    __tablename__ = f"{PREFIX}relationships"

    source_id: Mapped[uuid4] = mapped_column(UUID(as_uuid=True), ForeignKey(f"{PREFIX}bookmarks.id"), primary_key=True)
    target_id: Mapped[uuid4] = mapped_column(UUID(as_uuid=True), ForeignKey(f"{PREFIX}bookmarks.id"), primary_key=True)
    relationship_type: Mapped[str] = mapped_column(String(50), nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    source = relationship("Bookmark", foreign_keys=[source_id], back_populates="relationships")
    target = relationship("Bookmark", foreign_keys=[target_id])

# Create tables if they don't exist (useful for first deploy)
if not inspect(engine).has_table(f"{PREFIX}users"):
    Base.metadata.create_all(bind=engine)
