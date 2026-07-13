from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import UsuarioDB
from app.schemas import LoginRequest, TokenResponse, UsuarioCreate, UsuarioResponse
from app.auth import hash_password, verificar_password, criar_token_acesso, get_current_user, verificar_rate_limit, registrar_tentativa

router = APIRouter(prefix="/auth", tags=["Autenticação"])


@router.post("/cadastro", response_model=UsuarioResponse)
def cadastrar_usuario(
    dados: UsuarioCreate,
    db: Session = Depends(get_db),
    admin: UsuarioDB = Depends(get_current_user),
):
    if admin.role != "admin":
        raise HTTPException(status_code=403, detail="Apenas administradores podem cadastrar usuários")
    if db.query(UsuarioDB).filter(UsuarioDB.username == dados.username).first():
        raise HTTPException(status_code=400, detail="Username já existe")
    usuario = UsuarioDB(
        username=dados.username,
        nome=dados.nome,
        hashed_password=hash_password(dados.password),
        role=dados.role,
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return usuario


@router.post("/login", response_model=TokenResponse)
def login(dados: LoginRequest, db: Session = Depends(get_db)):
    verificar_rate_limit(dados.username)

    usuario = db.query(UsuarioDB).filter(UsuarioDB.username == dados.username).first()
    if not usuario or not verificar_password(dados.password, usuario.hashed_password):
        registrar_tentativa(dados.username, sucesso=False)
        raise HTTPException(status_code=401, detail="Usuário ou senha inválidos")

    if not usuario.ativo:
        raise HTTPException(status_code=401, detail="Usuário inativo")

    registrar_tentativa(dados.username, sucesso=True)
    token = criar_token_acesso({"sub": usuario.username, "id": usuario.id, "role": usuario.role})
    return TokenResponse(access_token=token, usuario=usuario)


@router.get("/me", response_model=UsuarioResponse)
def usuario_logado(usuario: UsuarioDB = Depends(get_current_user)):
    return usuario
