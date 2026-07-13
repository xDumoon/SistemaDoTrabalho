import os
import json
import time
from datetime import datetime, timedelta, timezone
from collections import defaultdict
from pathlib import Path
import bcrypt
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import UsuarioDB

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError(
        "SECRET_KEY não definida! Crie um arquivo .env na raiz com SECRET_KEY=seu_valor_aqui\n"
        "Gere uma chave com: python -c \"import secrets; print(secrets.token_hex(32))\""
    )

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("TOKEN_EXPIRE_MINUTES", "480"))

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

_RATE_LIMIT_FILE = Path(__file__).parent / ".rate_limit.json"
MAX_TENTATIVAS = 5
BLOCO_MINUTOS = 15


def _carregar_tentativas() -> dict[str, list[float]]:
    try:
        with open(_RATE_LIMIT_FILE) as f:
            dados = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    agora = time.time()
    return {
        k: [t for t in v if agora - t < BLOCO_MINUTOS * 60]
        for k, v in dados.items()
    }


def _salvar_tentativas(tentativas: dict[str, list[float]]):
    with open(_RATE_LIMIT_FILE, "w") as f:
        json.dump(tentativas, f)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verificar_password(password: str, hash_: str) -> bool:
    return bcrypt.checkpw(password.encode(), hash_.encode())


def verificar_rate_limit(username: str):
    agora = time.time()
    tentativas = _carregar_tentativas()
    tentativas[username] = [t for t in tentativas.get(username, []) if agora - t < BLOCO_MINUTOS * 60]
    _salvar_tentativas(tentativas)
    if len(tentativas[username]) >= MAX_TENTATIVAS:
        raise HTTPException(
            status_code=429,
            detail=f"Conta temporariamente bloqueada. Tente novamente em {BLOCO_MINUTOS} minutos."
        )


def registrar_tentativa(username: str, sucesso: bool):
    tentativas = _carregar_tentativas()
    if sucesso:
        tentativas.pop(username, None)
    else:
        tentativas.setdefault(username, []).append(time.time())
    _salvar_tentativas(tentativas)


def criar_token_acesso(data: dict) -> str:
    to_encode = data.copy()
    expira = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expira})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decodificar_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> UsuarioDB:
    payload = decodificar_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
        )
    username: str = payload.get("sub")
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
        )
    usuario = db.query(UsuarioDB).filter(UsuarioDB.username == username).first()
    if not usuario or not usuario.ativo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não encontrado ou inativo",
        )
    return usuario
