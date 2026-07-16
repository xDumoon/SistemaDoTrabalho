from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import ClienteDB, LogDB, UsuarioDB
from app.schemas import ClienteCreate, ClienteUpdate, ClienteResponse
from app.auth import get_current_user

router = APIRouter(prefix="/clientes", tags=["Clientes"])


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


@router.post("/", response_model=ClienteResponse)
def cadastrar_cliente(
    cliente: ClienteCreate,
    db: Session = Depends(get_db),
    usuario: UsuarioDB = Depends(get_current_user),
):
    if db.query(ClienteDB).filter(ClienteDB.cpf == cliente.cpf).first():
        raise HTTPException(status_code=400, detail="CPF já cadastrado")
    dados = cliente.model_dump(mode="json")
    dados["usuario_id"] = usuario.id
    novo = ClienteDB(**dados)
    db.add(novo)
    db.commit()
    db.refresh(novo)
    registrar_log(db, usuario, "criar", "cliente", novo.id, f"Cliente {novo.nome} cadastrado")
    return novo


@router.get("/", response_model=list[ClienteResponse])
def listar_clientes(
    q: str | None = None,
    db: Session = Depends(get_db),
    usuario: UsuarioDB = Depends(get_current_user),
):
    query = db.query(ClienteDB)
    if q:
        query = query.filter(
            ClienteDB.nome.ilike(f"%{q}%") | ClienteDB.cpf.ilike(f"%{q}%")
        )
    return query.all()


@router.get("/pendentes")
def listar_clientes_pendentes(
    db: Session = Depends(get_db),
    usuario: UsuarioDB = Depends(get_current_user),
):
    clientes = db.query(ClienteDB).all()
    resultado = []
    for c in clientes:
        tem_servico = any(s.status == "Pendente" for s in c.servicos)
        tem_emprestimo = any(e.status == "Pendente" for e in c.emprestimos)
        if tem_servico or tem_emprestimo:
            resultado.append({"id": c.id, "nome": c.nome, "cpf": c.cpf})
    return resultado


@router.get("/{cliente_id}", response_model=ClienteResponse)
def obter_cliente(
    cliente_id: int,
    db: Session = Depends(get_db),
    usuario: UsuarioDB = Depends(get_current_user),
):
    cliente = db.query(ClienteDB).filter(ClienteDB.id == cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    return cliente


@router.put("/{cliente_id}", response_model=ClienteResponse)
def atualizar_cliente(
    cliente_id: int,
    dados: ClienteUpdate,
    db: Session = Depends(get_db),
    usuario: UsuarioDB = Depends(get_current_user),
):
    cliente = db.query(ClienteDB).filter(ClienteDB.id == cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    for key, value in dados.model_dump(exclude_unset=True).items():
        setattr(cliente, key, value)
    db.commit()
    db.refresh(cliente)
    registrar_log(db, usuario, "atualizar", "cliente", cliente.id)
    return cliente


@router.delete("/{cliente_id}")
def deletar_cliente(
    cliente_id: int,
    db: Session = Depends(get_db),
    usuario: UsuarioDB = Depends(get_current_user),
):
    cliente = db.query(ClienteDB).filter(ClienteDB.id == cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    db.delete(cliente)
    db.commit()
    registrar_log(db, usuario, "deletar", "cliente", cliente_id, f"Cliente {cliente.nome} removido")
    return {"mensagem": "Cliente excluído com sucesso!"}


@router.get("/{cliente_id}/historico")
def ver_historico_cliente(
    cliente_id: int,
    db: Session = Depends(get_db),
    usuario: UsuarioDB = Depends(get_current_user),
):
    cliente = db.query(ClienteDB).filter(ClienteDB.id == cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    servicos = [
        {
            "id": s.id,
            "tipo_servico": s.tipo_servico,
            "status": s.status,
            "valor_cobrado": s.valor_cobrado or 0,
            "pago": s.pago or False,
            "observacoes": s.observacoes,
            "data_cadastro": s.data_cadastro.isoformat() if s.data_cadastro else None,
            "cliente_id": s.cliente_id,
        }
        for s in cliente.servicos
    ]
    emprestimos = [
        {
            "id": e.id,
            "banco": e.banco,
            "valor": e.valor,
            "comissao": e.comissao or 0,
            "parcelas": e.parcelas,
            "status": e.status,
            "data_cadastro": e.data_cadastro.isoformat() if e.data_cadastro else None,
            "data_conclusao": e.data_conclusao.isoformat() if e.data_conclusao else None,
            "cliente_id": e.cliente_id,
        }
        for e in cliente.emprestimos
    ]
    return {
        "cliente_nome": cliente.nome,
        "cpf": cliente.cpf,
        "telefone": cliente.telefone,
        "email": cliente.email,
        "endereco": cliente.endereco,
        "data_nascimento": cliente.data_nascimento,
        "observacoes": cliente.observacoes,
        "servicos": servicos,
        "emprestimos": emprestimos,
    }
