import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.database import engine, Base
from app.models import UsuarioDB
from app.auth import hash_password
from app.database import SessionLocal
from app.migrate import executar_migracoes
from app.routers import auth_router, clientes, servicos, emprestimos, dashboard

app = FastAPI(title="Credmax - Sistema de Gestão", version="2.0.0")

ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[ALLOWED_ORIGINS] if ALLOWED_ORIGINS != "*" else ["*"],
    allow_credentials=ALLOWED_ORIGINS != "*",
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)
executar_migracoes()


def criar_admin_inicial():
    db = SessionLocal()
    if not db.query(UsuarioDB).filter(UsuarioDB.username == "admin").first():
        admin_senha = os.getenv("ADMIN_PASSWORD", "admin123")
        admin = UsuarioDB(
            username="admin",
            nome="Administrador",
            hashed_password=hash_password(admin_senha),
            role="admin",
        )
        db.add(admin)
        db.commit()
    db.close()


criar_admin_inicial()

STATIC_DIR = Path(__file__).parent / "static"
STATIC_DIR.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/")
def servir_frontend():
    return FileResponse(str(STATIC_DIR / "index.html"))

app.include_router(auth_router.router)
app.include_router(clientes.router)
app.include_router(servicos.router)
app.include_router(emprestimos.router)
app.include_router(dashboard.router)
