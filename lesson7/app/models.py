from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


class QuoteRow(Base):
    __tablename__ = "quotes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    source_url: Mapped[str] = mapped_column(String(512), nullable=False, index=True)
    quote: Mapped[str] = mapped_column(Text, nullable=False)
    author: Mapped[str] = mapped_column(String(255), nullable=False)
    tags: Mapped[str] = mapped_column(Text, nullable=False, default="")
    author_url: Mapped[str] = mapped_column(String(512), nullable=False, default="")
    page: Mapped[int] = mapped_column(Integer, nullable=False)
    scraped_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class ParseRun(Base):
    __tablename__ = "parse_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    source_url: Mapped[str] = mapped_column(String(512), nullable=False)
    login_ok: Mapped[str] = mapped_column(String(10), nullable=False)
    total_quotes: Mapped[int] = mapped_column(Integer, nullable=False)
    total_requests: Mapped[int] = mapped_column(Integer, nullable=False)
    http_requests: Mapped[int] = mapped_column(Integer, nullable=False)
    https_requests: Mapped[int] = mapped_column(Integer, nullable=False)
    responses_2xx: Mapped[int] = mapped_column(Integer, nullable=False)
    responses_3xx: Mapped[int] = mapped_column(Integer, nullable=False)
    redirects_http_to_https: Mapped[int] = mapped_column(Integer, nullable=False)
    avg_http_size: Mapped[int] = mapped_column(Integer, nullable=False)
    avg_https_size: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
