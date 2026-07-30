"""SQLAlchemy ORM models — durable user data (not cache)."""

from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(256))

    # Optional linked Riot ID so the app can open on their own profile.
    riot_region: Mapped[str | None] = mapped_column(String(10), default=None)
    riot_name: Mapped[str | None] = mapped_column(String(64), default=None)
    riot_tag: Mapped[str | None] = mapped_column(String(16), default=None)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class SavedPool(Base):
    """A user's champion pool preset for a specific role."""

    __tablename__ = "saved_pools"
    __table_args__ = (UniqueConstraint("user_id", "role"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    role: Mapped[str] = mapped_column(String(10))  # TOP / JUNGLE / MID / BOT / SUPPORT
    champions: Mapped[list] = mapped_column(JSON, default=list)  # ["Aatrox", "Darius", ...]
