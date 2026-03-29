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
