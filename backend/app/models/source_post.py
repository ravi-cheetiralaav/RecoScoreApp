"""SourcePost model - raw posts from ingestion source."""
from datetime import datetime
from sqlalchemy import String, Text, DateTime, Boolean, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class SourcePost(Base):
    __tablename__ = "source_posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    external_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    source: Mapped[str] = mapped_column(String(50), default="mock")  # facebook | mock
    raw_text: Mapped[str] = mapped_column(Text)
    post_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    posted_at: Mapped[datetime] = mapped_column(DateTime)
    ingested_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    is_processed: Mapped[bool] = mapped_column(Boolean, default=False)
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON blob

    # Relationships
    recommendations = relationship("Recommendation", back_populates="source_post")
    extraction_audits = relationship("ExtractionAudit", back_populates="source_post")
