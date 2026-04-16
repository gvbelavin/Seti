from urllib.parse import urlparse

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from .db import Base, engine, get_db
from .models import ParseRun, QuoteRow
from .parser_service import run_parser
from .schemas import ParseResponse, QuoteOut


app = FastAPI(title="Lesson5 Parser API")


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)


@app.get("/")
def root():
    return {"message": "Lesson5 parser API is running"}


@app.get("/parse", response_model=ParseResponse)
def parse_url(
    url: str = Query(..., description="Пример: https://quotes.toscrape.com"),
    username: str = Query("admin"),
    password: str = Query("admin"),
    db: Session = Depends(get_db),
):
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise HTTPException(status_code=400, detail="Нужен корректный URL с http:// или https://")

    try:
        quotes_data, stats = run_parser(url, username, password)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Ошибка парсера: {exc}") from exc

    if not quotes_data:
        raise HTTPException(status_code=400, detail="Парсер не нашел данные. Проверьте URL и структуру сайта.")

    for quote in quotes_data:
        db.add(
            QuoteRow(
                source_url=url,
                quote=quote["quote"],
                author=quote["author"],
                tags=quote["tags"],
                author_url=quote["author_url"],
                page=int(quote["page"]),
                scraped_at=quote["scraped_at"],
            )
        )

    db.add(
        ParseRun(
            source_url=url,
            login_ok=str(stats["login_ok"]).lower(),
            total_quotes=stats["total_quotes"],
            total_requests=stats["total_requests"],
            http_requests=stats["http_requests"],
            https_requests=stats["https_requests"],
            responses_2xx=stats["responses_2xx"],
            responses_3xx=stats["responses_3xx"],
            redirects_http_to_https=stats["redirects_http_to_https"],
            avg_http_size=stats["avg_http_size"],
            avg_https_size=stats["avg_https_size"],
        )
    )
    db.commit()

    return ParseResponse(
        message="Парсинг завершен, данные записаны в БД",
        source_url=url,
        login_ok=stats["login_ok"],
        saved_quotes=len(quotes_data),
        total_requests=stats["total_requests"],
        http_requests=stats["http_requests"],
        https_requests=stats["https_requests"],
    )


@app.get("/quotes", response_model=list[QuoteOut])
def get_quotes(limit: int = Query(100, ge=1, le=1000), db: Session = Depends(get_db)):
    rows = db.execute(select(QuoteRow).order_by(QuoteRow.id.desc()).limit(limit)).scalars().all()
    return rows


@app.get("/runs")
def get_runs(limit: int = Query(20, ge=1, le=200), db: Session = Depends(get_db)):
    rows = db.execute(select(ParseRun).order_by(ParseRun.id.desc()).limit(limit)).scalars().all()
    return [
        {
            "id": r.id,
            "source_url": r.source_url,
            "login_ok": r.login_ok,
            "total_quotes": r.total_quotes,
            "total_requests": r.total_requests,
            "http_requests": r.http_requests,
            "https_requests": r.https_requests,
            "responses_2xx": r.responses_2xx,
            "responses_3xx": r.responses_3xx,
            "redirects_http_to_https": r.redirects_http_to_https,
            "avg_http_size": r.avg_http_size,
            "avg_https_size": r.avg_https_size,
            "created_at": r.created_at,
        }
        for r in rows
    ]
