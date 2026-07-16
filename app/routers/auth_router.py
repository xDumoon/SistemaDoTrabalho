from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
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


@router.get("/usuarios", response_model=list[UsuarioResponse])
def listar_usuarios(
    db: Session = Depends(get_db),
    admin: UsuarioDB = Depends(get_current_user),
):
    if admin.role != "admin":
        raise HTTPException(status_code=403, detail="Apenas administradores")
    return db.query(UsuarioDB).all()


@router.delete("/usuarios/{usuario_id}")
def deletar_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    admin: UsuarioDB = Depends(get_current_user),
):
    if admin.role != "admin":
        raise HTTPException(status_code=403, detail="Apenas administradores")
    if usuario_id == admin.id:
        raise HTTPException(status_code=400, detail="Não é possível excluir a si mesmo")
    usuario = db.query(UsuarioDB).filter(UsuarioDB.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    db.delete(usuario)
    db.commit()
    return {"mensagem": "Usuário excluído com sucesso!"}


class AlterarSenhaRequest(BaseModel):
    nova_senha: str = Field(..., min_length=4, max_length=100)


@router.put("/usuarios/{usuario_id}/senha")
def alterar_senha_usuario(
    usuario_id: int,
    dados: AlterarSenhaRequest,
    db: Session = Depends(get_db),
    admin: UsuarioDB = Depends(get_current_user),
):
    if admin.role != "admin":
        raise HTTPException(status_code=403, detail="Apenas administradores podem alterar senhas")
    usuario = db.query(UsuarioDB).filter(UsuarioDB.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    usuario.hashed_password = hash_password(dados.nova_senha)
    db.commit()
    return {"mensagem": f"Senha de {usuario.nome} alterada com sucesso!"}
