from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import PedidoAposentadoriaDB, LogDB, UsuarioDB
from app.schemas import PedidoAposentadoriaCreate, PedidoAposentadoriaUpdate, PedidoAposentadoriaResponse
from app.auth import get_current_user

router = APIRouter(prefix="/pedidos-aposentadoria", tags=["Pedidos de Aposentadoria"])


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


@router.post("/", response_model=PedidoAposentadoriaResponse)
def criar_pedido(
    pedido: PedidoAposentadoriaCreate,
    db: Session = Depends(get_db),
    usuario: UsuarioDB = Depends(get_current_user),
):
    novo = PedidoAposentadoriaDB(**pedido.model_dump(), usuario_id=usuario.id)
    db.add(novo)
    db.commit()
    db.refresh(novo)
    registrar_log(db, usuario, "criar", "pedido_aposentadoria", novo.id, f"Pedido: {novo.nome_cliente}")
    return novo


@router.get("/", response_model=list[PedidoAposentadoriaResponse])
def listar_pedidos(
    db: Session = Depends(get_db),
    usuario: UsuarioDB = Depends(get_current_user),
):
    query = db.query(PedidoAposentadoriaDB)
    if usuario.role != "admin":
        query = query.filter(PedidoAposentadoriaDB.usuario_id == usuario.id)
    return query.order_by(PedidoAposentadoriaDB.id.desc()).all()


@router.put("/{pedido_id}", response_model=PedidoAposentadoriaResponse)
def atualizar_pedido(
    pedido_id: int,
    dados: PedidoAposentadoriaUpdate,
    db: Session = Depends(get_db),
    usuario: UsuarioDB = Depends(get_current_user),
):
    pedido = db.query(PedidoAposentadoriaDB).filter(PedidoAposentadoriaDB.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    if dados.nome_cliente is not None:
        pedido.nome_cliente = dados.nome_cliente
    if dados.cpf is not None:
        pedido.cpf = dados.cpf
    if dados.telefone is not None:
        pedido.telefone = dados.telefone
    if dados.observacoes is not None:
        pedido.observacoes = dados.observacoes
    if dados.status is not None:
        pedido.status = dados.status
    db.commit()
    db.refresh(pedido)
    registrar_log(db, usuario, "atualizar", "pedido_aposentadoria", pedido.id, f"Pedido atualizado: {pedido.nome_cliente}")
    return pedido


@router.delete("/{pedido_id}")
def deletar_pedido(
    pedido_id: int,
    db: Session = Depends(get_db),
    usuario: UsuarioDB = Depends(get_current_user),
):
    pedido = db.query(PedidoAposentadoriaDB).filter(PedidoAposentadoriaDB.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    db.delete(pedido)
    db.commit()
    registrar_log(db, usuario, "deletar", "pedido_aposentadoria", pedido_id)
    return {"mensagem": "Pedido excluído com sucesso!"}
