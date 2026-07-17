from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from app.database import get_db
from app.models import PedidoAposentadoriaDB, ClienteDB, LogDB, UsuarioDB
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


def _to_response(pedido):
    c = pedido.cliente
    return PedidoAposentadoriaResponse(
        id=pedido.id,
        cliente_id=pedido.cliente_id,
        cliente_nome=c.nome if c else None,
        cliente_cpf=c.cpf if c else None,
        cliente_telefone=c.telefone if c else None,
        valor_cobrado=pedido.valor_cobrado or 0.0,
        pago=pedido.pago or False,
        observacoes=pedido.observacoes,
        status=pedido.status,
        data_cadastro=pedido.data_cadastro,
        data_conclusao=pedido.data_conclusao,
    )


@router.post("/", response_model=PedidoAposentadoriaResponse)
def criar_pedido(
    pedido: PedidoAposentadoriaCreate,
    db: Session = Depends(get_db),
    usuario: UsuarioDB = Depends(get_current_user),
):
    cliente = db.query(ClienteDB).filter(ClienteDB.id == pedido.cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    novo = PedidoAposentadoriaDB(**pedido.model_dump(), usuario_id=usuario.id)
    db.add(novo)
    db.commit()
    db.refresh(novo)
    detalhes = f"Pedido aposentadoria: {cliente.nome}"
    if novo.valor_cobrado > 0:
        detalhes += f" - R${novo.valor_cobrado:.2f} {'(PAGO)' if novo.pago else '(PENDENTE)'}"
    registrar_log(db, usuario, "criar", "pedido_aposentadoria", novo.id, detalhes)
    return _to_response(novo)


@router.get("/", response_model=list[PedidoAposentadoriaResponse])
def listar_pedidos(
    db: Session = Depends(get_db),
    usuario: UsuarioDB = Depends(get_current_user),
):
    query = db.query(PedidoAposentadoriaDB).options(joinedload(PedidoAposentadoriaDB.cliente))
    if usuario.role != "admin":
        query = query.filter(PedidoAposentadoriaDB.usuario_id == usuario.id)
    return [_to_response(p) for p in query.order_by(PedidoAposentadoriaDB.id.desc()).all()]


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
    if dados.cliente_id is not None:
        cliente = db.query(ClienteDB).filter(ClienteDB.id == dados.cliente_id).first()
        if not cliente:
            raise HTTPException(status_code=404, detail="Cliente não encontrado")
        pedido.cliente_id = dados.cliente_id
    if dados.valor_cobrado is not None:
        pedido.valor_cobrado = dados.valor_cobrado
    if dados.pago is not None:
        pedido.pago = dados.pago
    if dados.observacoes is not None:
        pedido.observacoes = dados.observacoes
    if dados.status is not None:
        pedido.status = dados.status
    db.commit()
    db.refresh(pedido)
    c = pedido.cliente
    registrar_log(db, usuario, "atualizar", "pedido_aposentadoria", pedido.id, f"Pedido atualizado: {c.nome if c else '-'}")
    return _to_response(pedido)


@router.put("/{pedido_id}/concluir", response_model=PedidoAposentadoriaResponse)
def concluir_pedido(
    pedido_id: int,
    db: Session = Depends(get_db),
    usuario: UsuarioDB = Depends(get_current_user),
):
    pedido = db.query(PedidoAposentadoriaDB).filter(PedidoAposentadoriaDB.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    pedido.status = "Concluído"
    pedido.data_conclusao = datetime.utcnow()
    db.commit()
    db.refresh(pedido)
    c = pedido.cliente
    registrar_log(db, usuario, "concluir", "pedido_aposentadoria", pedido.id, f"Pedido concluído: {c.nome if c else '-'}")
    return _to_response(pedido)


@router.put("/{pedido_id}/pagar", response_model=PedidoAposentadoriaResponse)
def marcar_pago(
    pedido_id: int,
    db: Session = Depends(get_db),
    usuario: UsuarioDB = Depends(get_current_user),
):
    pedido = db.query(PedidoAposentadoriaDB).filter(PedidoAposentadoriaDB.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    pedido.pago = True
    db.commit()
    db.refresh(pedido)
    c = pedido.cliente
    registrar_log(db, usuario, "pagar", "pedido_aposentadoria", pedido.id, f"Pedido pago: {c.nome if c else '-'} R${pedido.valor_cobrado:.2f}")
    return _to_response(pedido)


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
