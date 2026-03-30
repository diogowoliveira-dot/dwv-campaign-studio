import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

load_dotenv()

from routers import auth, executivos, campanhas
import db  # initializes the database

app = FastAPI(
    title="DWV Campaign Studio API",
    version="1.0.0",
    description="API para geração e edição conversacional de campanhas imobiliárias",
)

# CORS
origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:3333").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve local storage files
storage_dir = os.path.join(os.path.dirname(__file__), "storage")
os.makedirs(storage_dir, exist_ok=True)
app.mount("/storage", StaticFiles(directory=storage_dir), name="storage")

# Routers
app.include_router(auth.router, prefix="/auth", tags=["Autenticação"])
app.include_router(executivos.router, prefix="/executivos", tags=["Executivos"])
app.include_router(campanhas.router, prefix="/campanhas", tags=["Campanhas"])


@app.get("/")
async def root():
    return {"status": "ok", "app": "DWV Campaign Studio API"}


@app.get("/test-anthropic")
async def test_anthropic():
    """Test if we can reach Anthropic API."""
    import httpx
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    try:
        async with httpx.AsyncClient(timeout=30) as http:
            r = await http.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={"model": "claude-sonnet-4-20250514", "max_tokens": 10, "messages": [{"role": "user", "content": "hi"}]},
            )
            return {"status": r.status_code, "body": r.json() if r.status_code == 200 else r.text[:200]}
    except Exception as e:
        return {"status": "error", "type": type(e).__name__, "detail": str(e)}


@app.get("/health")
async def health():
    """Debug endpoint to test DB connection."""
    try:
        d = db.get_db()
        res = d.table("executivos").select("*").execute()
        api_key = os.getenv("ANTHROPIC_API_KEY", "")
        return {
            "db": "ok", "rows": len(res.data),
            "use_postgres": db.USE_POSTGRES,
            "has_db_url": bool(os.getenv("DATABASE_URL")),
            "has_anthropic_key": bool(api_key and api_key != "placeholder"),
            "anthropic_key_prefix": api_key[:15] + "..." if api_key else "MISSING",
        }
    except Exception as e:
        return {"db": "error", "detail": str(e), "use_postgres": db.USE_POSTGRES, "has_db_url": bool(os.getenv("DATABASE_URL"))}
