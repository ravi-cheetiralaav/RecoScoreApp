"""ExtractionAudit model - audit trail for LLM/rule extraction."""
from datetime import datetime
from sqlalchemy import String, Text, Float, Integer, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class ExtractionAudit(Base):
    __tablename__ = "extraction_audits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    source_post_id: Mapped[int] = mapped_column(Integer, ForeignKey("source_posts.id"), index=True)

    extraction_method: Mapped[str] = mapped_column(String(20))  # rule | llm
    prompt_version: Mapped[str | None] = mapped_column(String(20), nullable=True)
    raw_llm_output: Mapped[str | None] = mapped_column(Text, nullable=True)
    normalized_output: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    source_post = relationship("SourcePost", back_populates="extraction_audits")
