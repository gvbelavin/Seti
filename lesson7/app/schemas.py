from datetime import datetime

from pydantic import BaseModel


class QuoteOut(BaseModel):
    id: int
    source_url: str
    quote: str
    author: str
    tags: str
    author_url: str
    page: int
    scraped_at: datetime

    class Config:
        from_attributes = True


class ParseResponse(BaseModel):
    message: str
    source_url: str
    login_ok: bool
    saved_quotes: int
    total_requests: int
    http_requests: int
    https_requests: int
