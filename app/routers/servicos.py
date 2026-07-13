from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import ServicoDB, LogDB, UsuarioDB
from app.schemas import ServicoCreate, ServicoUpdate, ServicoResponse
from app.auth import get_current_user

router = APIRouter(prefix="/servicos", tags=["Serviços INSS"])


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


@router.post("/", response_model=ServicoResponse)
def cadastrar_servico(
    servico: ServicoCreate,
    db: Session = Depends(get_db),
    usuario: UsuarioDB = Depends(get_current_user),
):
    novo = ServicoDB(**servico.model_dump())
    db.add(novo)
    db.commit()
    db.refresh(novo)
    detalhes = f"Serviço {novo.tipo_servico}"
    if novo.valor_cobrado > 0:
        detalhes += f" - R${novo.valor_cobrado:.2f} {'(PAGO)' if novo.pago else '(PENDENTE)'}"
    registrar_log(db, usuario, "criar", "servico", novo.id, detalhes)
    return novo


@router.get("/{cliente_id}/servicos", response_model=list[ServicoResponse])
def listar_servicos_do_cliente(
    cliente_id: int,
    db: Session = Depends(get_db),
    usuario: UsuarioDB = Depends(get_current_user),
):
    return db.query(ServicoDB).filter(ServicoDB.cliente_id == cliente_id).all()


@router.get("/", response_model=list[ServicoResponse])
def listar_todos_servicos(
    db: Session = Depends(get_db),
    usuario: UsuarioDB = Depends(get_current_user),
):
    return db.query(ServicoDB).order_by(ServicoDB.id.desc()).limit(200).all()


@router.put("/{servico_id}/concluir", response_model=ServicoResponse)
def concluir_servico(
    servico_id: int,
    db: Session = Depends(get_db),
    usuario: UsuarioDB = Depends(get_current_user),
):
    servico = db.query(ServicoDB).filter(ServicoDB.id == servico_id).first()
    if not servico:
        raise HTTPException(status_code=404, detail="Serviço não encontrado")
    servico.status = "Concluído"
    db.commit()
    db.refresh(servico)
    registrar_log(db, usuario, "concluir", "servico", servico.id)
    return servico


@router.put("/{servico_id}/pagar", response_model=ServicoResponse)
def marcar_servico_pago(
    servico_id: int,
    db: Session = Depends(get_db),
    usuario: UsuarioDB = Depends(get_current_user),
):
    servico = db.query(ServicoDB).filter(ServicoDB.id == servico_id).first()
    if not servico:
        raise HTTPException(status_code=404, detail="Serviço não encontrado")
    servico.pago = True
    db.commit()
    db.refresh(servico)
    registrar_log(db, usuario, "pagar", "servico", servico.id,
                  f"Serviço {servico.tipo_servico} marcado como pago - R${servico.valor_cobrado:.2f}")
    return servico


@router.put("/{servico_id}/atualizar", response_model=ServicoResponse)
def atualizar_servico(
    servico_id: int,
    dados: ServicoUpdate,
    db: Session = Depends(get_db),
    usuario: UsuarioDB = Depends(get_current_user),
):
    servico = db.query(ServicoDB).filter(ServicoDB.id == servico_id).first()
    if not servico:
        raise HTTPException(status_code=404, detail="Serviço não encontrado")
    if dados.pago is not None:
        servico.pago = dados.pago
    if dados.status is not None:
        servico.status = dados.status
    db.commit()
    db.refresh(servico)
    return servico


@router.delete("/{servico_id}")
def deletar_servico(
    servico_id: int,
    db: Session = Depends(get_db),
    usuario: UsuarioDB = Depends(get_current_user),
):
    servico = db.query(ServicoDB).filter(ServicoDB.id == servico_id).first()
    if not servico:
        raise HTTPException(status_code=404, detail="Serviço não encontrado")
    db.delete(servico)
    db.commit()
    registrar_log(db, usuario, "deletar", "servico", servico_id)
    return {"mensagem": "Serviço excluído com sucesso!"}
