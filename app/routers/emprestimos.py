from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import EmprestimoDB, LogDB, UsuarioDB
from app.schemas import EmprestimoCreate, EmprestimoUpdate, EmprestimoResponse
from app.auth import get_current_user

router = APIRouter(prefix="/emprestimos", tags=["Empréstimos"])


def registrar_log(db, usuario, acao, entidade, entidade_id=None, detalhes=None):
    log = LogDB(
        usuario_id=usuario.id if usuario else None,
        usuario_nome=usuario.nome if usuario else None,
        acao=acao,
        entidade=entidade,
        entidade_id=entidade_id,
        detalhes=detalhes,
    )
    db.add(log)
    db.commit()


@router.post("/", response_model=EmprestimoResponse)
def cadastrar_emprestimo(
    emprestimo: EmprestimoCreate,
    db: Session = Depends(get_db),
    usuario: UsuarioDB = Depends(get_current_user),
):
    novo = EmprestimoDB(**emprestimo.model_dump())
    db.add(novo)
    db.commit()
    db.refresh(novo)
    detalhes = f"Empréstimo R${novo.valor:.2f} - {novo.banco}"
    if novo.comissao > 0:
        detalhes += f" (comissão: R${novo.comissao:.2f})"
    registrar_log(db, usuario, "criar", "emprestimo", novo.id, detalhes)
    return novo


@router.get("/", response_model=list[EmprestimoResponse])
def listar_emprestimos(
    db: Session = Depends(get_db),
    usuario: UsuarioDB = Depends(get_current_user),
):
    return db.query(EmprestimoDB).order_by(EmprestimoDB.id.desc()).limit(200).all()


@router.put("/{emprestimo_id}/concluir", response_model=EmprestimoResponse)
def concluir_emprestimo(
    emprestimo_id: int,
    db: Session = Depends(get_db),
    usuario: UsuarioDB = Depends(get_current_user),
):
    emprestimo = db.query(EmprestimoDB).filter(EmprestimoDB.id == emprestimo_id).first()
    if not emprestimo:
        raise HTTPException(status_code=404, detail="Empréstimo não encontrado")
    emprestimo.status = "Concluído"
    emprestimo.data_conclusao = datetime.utcnow()
    db.commit()
    db.refresh(emprestimo)
    registrar_log(db, usuario, "concluir", "emprestimo", emprestimo.id)
    return emprestimo


@router.put("/{emprestimo_id}", response_model=EmprestimoResponse)
def atualizar_emprestimo(
    emprestimo_id: int,
    dados: EmprestimoUpdate,
    db: Session = Depends(get_db),
    usuario: UsuarioDB = Depends(get_current_user),
):
    emprestimo = db.query(EmprestimoDB).filter(EmprestimoDB.id == emprestimo_id).first()
    if not emprestimo:
        raise HTTPException(status_code=404, detail="Empréstimo não encontrado")
    if dados.comissao is not None:
        emprestimo.comissao = dados.comissao
    if dados.status is not None:
        emprestimo.status = dados.status
    db.commit()
    db.refresh(emprestimo)
    registrar_log(db, usuario, "atualizar", "emprestimo", emprestimo.id)
    return emprestimo


@router.delete("/{emprestimo_id}")
def deletar_emprestimo(
    emprestimo_id: int,
    db: Session = Depends(get_db),
    usuario: UsuarioDB = Depends(get_current_user),
):
    emprestimo = db.query(EmprestimoDB).filter(EmprestimoDB.id == emprestimo_id).first()
    if not emprestimo:
        raise HTTPException(status_code=404, detail="Empréstimo não encontrado")
    db.delete(emprestimo)
    db.commit()
    registrar_log(db, usuario, "deletar", "emprestimo", emprestimo_id)
    return {"mensagem": "Empréstimo excluído com sucesso!"}
