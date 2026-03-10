import uuid
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from models import (
    Bookmark,
    SessionLocal,
    Summary,
    Tag,
    User,
    bookmark_tag,
    engine,
)
from ai_service import generate_summary, expand_search_query

router = APIRouter(prefix="/api/v1", tags=["LinkSage"])

# Dependency to get a DB session per request
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------
class CreateBookmarkRequest(BaseModel):
    url: str = Field(..., description="Fully qualified URL to bookmark")
    title: str | None = Field(None, description="Optional title; if omitted we use the URL host")
    tags: list[str] | None = Field(default_factory=list, description="Optional initial tags")

class BookmarkResponse(BaseModel):
    id: uuid.UUID
    url: str
    title: str
    summary: str | None = None
    tags: list[str] = []

class SummarizeRequest(BaseModel):
    url: str = Field(..., description="URL to summarize")

class SummarizeResponse(BaseModel):
    summary: str
    note: str | None = None

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=3)
    sort_by: str | None = None
    page: int = Field(1, ge=1)

class SearchResult(BaseModel):
    id: uuid.UUID
    title: str
    score: float
    why_relevant: str | None = None

class SearchResponse(BaseModel):
    results: list[SearchResult]
    query_expanded: str | None = None

# ---------------------------------------------------------------------------
# Helper – get a dummy user (authentication omitted for brevity)
# ---------------------------------------------------------------------------
def get_dummy_user(db: Session) -> User:
    user = db.query(User).first()
    if not user:
        # create a placeholder user
        user = User(email="demo@example.com", password_hash="not_hashed")
        db.add(user)
        db.commit()
        db.refresh(user)
    return user

# ---------------------------------------------------------------------------
# Endpoint: Create Bookmark – triggers AI summary & tag generation
# ---------------------------------------------------------------------------
@router.post("/bookmarks", response_model=BookmarkResponse, status_code=status.HTTP_201_CREATED)
async def create_bookmark(payload: CreateBookmarkRequest, db: Session = Depends(get_db)):
    user = get_dummy_user(db)
    # Basic validation – ensure URL uniqueness per user
    existing = db.query(Bookmark).filter(Bookmark.user_id == user.id, Bookmark.url == payload.url).first()
    if existing:
        raise HTTPException(status_code=400, detail="Bookmark already exists for this user")

    title = payload.title or payload.url.split("//")[-1].split("/")[0]
    bookmark = Bookmark(user_id=user.id, url=payload.url, title=title)
    db.add(bookmark)
    db.commit()
    db.refresh(bookmark)

    # ------------------ AI Summary ------------------
    summary_data = await generate_summary(payload.url)
    summary_text = summary_data.get("summary") or summary_data.get("note") or ""
    summary = Summary(
        bookmark_id=bookmark.id,
        content=summary_text,
        confidence_score=summary_data.get("confidence_score", 0.0),
        model_version=summary_data.get("model_version", "unknown"),
    )
    db.add(summary)
    db.commit()

    # ------------------ Tags (AI + user supplied) ------------------
    tag_names: set[str] = set(payload.tags or [])
    # Simple heuristic: split summary into words and take unique nouns (placeholder)
    # In a real system we would ask the AI for tags; here we just echo back.
    for tag_name in tag_names:
        tag = db.query(Tag).filter(Tag.name == tag_name, Tag.type == "user_defined").first()
        if not tag:
            tag = Tag(name=tag_name, type="user_defined")
            db.add(tag)
            db.commit()
            db.refresh(tag)
        # associate via association table
        ins = bookmark_tag.insert().values(
            bookmark_id=bookmark.id,
            tag_id=tag.id,
            confidence_score=1.0,
            is_primary=False,
        )
        db.execute(ins)
    db.commit()

    # Prepare response
    resp = BookmarkResponse(
        id=bookmark.id,
        url=bookmark.url,
        title=bookmark.title,
        summary=summary.content,
        tags=[t.name for t in bookmark.tags],
    )
    return resp

# ---------------------------------------------------------------------------
# Endpoint: Retrieve a Bookmark
# ---------------------------------------------------------------------------
@router.get("/bookmarks/{bookmark_id}", response_model=BookmarkResponse)
def get_bookmark(bookmark_id: uuid.UUID, db: Session = Depends(get_db)):
    bookmark = db.query(Bookmark).filter(Bookmark.id == bookmark_id).first()
    if not bookmark:
        raise HTTPException(status_code=404, detail="Bookmark not found")
    summary = bookmark.summary.content if bookmark.summary else None
    return BookmarkResponse(
        id=bookmark.id,
        url=bookmark.url,
        title=bookmark.title,
        summary=summary,
        tags=[t.name for t in bookmark.tags],
    )

# ---------------------------------------------------------------------------
# Endpoint: Stand‑alone Summarization (useful for external callers)
# ---------------------------------------------------------------------------
@router.post("/summarize", response_model=SummarizeResponse)
async def summarize_endpoint(req: SummarizeRequest):
    result = await generate_summary(req.url)
    if "summary" in result:
        return SummarizeResponse(summary=result["summary"])
    return SummarizeResponse(summary="", note=result.get("note", "AI unavailable"))

# ---------------------------------------------------------------------------
# Endpoint: Smart Search with AI query expansion
# ---------------------------------------------------------------------------
@router.post("/search", response_model=SearchResponse)
async def smart_search(req: SearchRequest, db: Session = Depends(get_db)):
    # Expand the query via AI
    expansion = await expand_search_query(req.query)
    expanded_query = expansion.get("expanded_query") or req.query

    # NOTE: Real implementation would query Elasticsearch. Here we return a stub.
    # For demo we fetch up to 5 recent bookmarks containing the original query string.
    like_pattern = f"%{req.query}%"
    bookmarks = (
        db.query(Bookmark)
        .filter(Bookmark.title.ilike(like_pattern) | Bookmark.url.ilike(like_pattern))
        .order_by(Bookmark.created_at.desc())
        .limit(5)
        .all()
    )
    results = []
    for bm in bookmarks:
        results.append(
            SearchResult(
                id=bm.id,
                title=bm.title,
                score=0.8,  # placeholder score
                why_relevant="Title or URL matched query terms",
            )
        )
    return SearchResponse(results=results, query_expanded=expanded_query)
