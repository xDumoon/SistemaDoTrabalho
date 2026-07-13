import csv
import io
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models import ClienteDB, ServicoDB, EmprestimoDB, LogDB, UsuarioDB
from app.schemas import DashboardResponse, LogResponse
from app.auth import get_current_user


def _sanitizar_csv(valor) -> str:
    s = str(valor) if valor is not None else ""
    if s and s[0] in ("=", "+", "-", "@", "\t", "\r", "\n"):
        s = "'" + s
    return s

router = APIRouter(tags=["Dashboard e Utilitários"])


@router.get("/dashboard", response_model=DashboardResponse)
def obter_dashboard(
    db: Session = Depends(get_db),
    usuario: UsuarioDB = Depends(get_current_user),
):
    total_clientes = db.query(ClienteDB).count()
    servicos_pend = db.query(ServicoDB).filter(ServicoDB.status == "Pendente").count()
    emprestimos_pend = db.query(EmprestimoDB).filter(EmprestimoDB.status == "Pendente").count()
    emprestimos_conc = db.query(EmprestimoDB).filter(EmprestimoDB.status == "Concluído").count()
    total_emprestimos = db.query(func.sum(EmprestimoDB.valor)).scalar() or 0.0

    trinta_dias_atras = datetime.utcnow() - timedelta(days=30)

    # Total de empréstimos no mês
    total_emp_mes = db.query(func.sum(EmprestimoDB.valor)).filter(
        EmprestimoDB.data_cadastro >= trinta_dias_atras
    ).scalar() or 0.0

    # Comissões
    comissao_total = db.query(func.sum(EmprestimoDB.comissao)).scalar() or 0.0
    comissao_mes = db.query(func.sum(EmprestimoDB.comissao)).filter(
        EmprestimoDB.data_cadastro >= trinta_dias_atras
    ).scalar() or 0.0

    # Receita de serviços
    receita_mes = db.query(func.sum(ServicoDB.valor_cobrado)).filter(
        ServicoDB.pago == True,
        ServicoDB.data_cadastro >= trinta_dias_atras
    ).scalar() or 0.0

    receita_total = db.query(func.sum(ServicoDB.valor_cobrado)).filter(
        ServicoDB.pago == True
    ).scalar() or 0.0

    servicos_pagos_mes = db.query(func.sum(ServicoDB.valor_cobrado)).filter(
        ServicoDB.pago == True,
        ServicoDB.status == "Concluído",
        ServicoDB.data_cadastro >= trinta_dias_atras
    ).scalar() or 0.0

    a_receber = db.query(func.sum(ServicoDB.valor_cobrado)).filter(
        ServicoDB.pago == False,
        ServicoDB.valor_cobrado > 0
    ).scalar() or 0.0

    return DashboardResponse(
        total_clientes=total_clientes,
        servicos_pendentes=servicos_pend,
        emprestimos_pendentes=emprestimos_pend,
        pendencias_totais=servicos_pend + emprestimos_pend,
        total_emprestimos=total_emprestimos,
        total_emprestimos_mes=total_emp_mes,
        emprestimos_concluidos=emprestimos_conc,
        comissao_total=comissao_total,
        comissao_mes=comissao_mes,
        receita_servicos_mes=receita_mes,
        receita_servicos_total=receita_total,
        servicos_pagos_mes=servicos_pagos_mes,
        servicos_a_receber=a_receber,
    )


@router.get("/receita-servicos")
def relatorio_receita_servicos(
    periodo: str = Query("total", pattern="^(mes|total)$"),
    db: Session = Depends(get_db),
    usuario: UsuarioDB = Depends(get_current_user),
):
    query = db.query(
        ServicoDB.tipo_servico,
        func.count(ServicoDB.id).label("quantidade"),
        func.sum(ServicoDB.valor_cobrado).label("total"),
        func.sum(ServicoDB.valor_cobrado).filter(ServicoDB.pago == True).label("recebido"),
        func.sum(ServicoDB.valor_cobrado).filter(ServicoDB.pago == False).label("a_receber"),
    )

    if periodo == "mes":
        trinta_dias = datetime.utcnow() - timedelta(days=30)
        query = query.filter(ServicoDB.data_cadastro >= trinta_dias)

    resultados = query.group_by(ServicoDB.tipo_servico).all()

    return [
        {
            "tipo": r.tipo_servico,
            "quantidade": r.quantidade,
            "total": float(r.total or 0),
            "recebido": float(r.recebido or 0),
            "a_receber": float(r.a_receber or 0),
        }
        for r in resultados
    ]


@router.get("/logs", response_model=list[LogResponse])
def listar_logs(
    limite: int = Query(50, le=200),
    db: Session = Depends(get_db),
    usuario: UsuarioDB = Depends(get_current_user),
):
    return db.query(LogDB).order_by(LogDB.id.desc()).limit(limite).all()


@router.get("/exportar/clientes")
def exportar_clientes_csv(
    db: Session = Depends(get_db),
    usuario: UsuarioDB = Depends(get_current_user),
):
    clientes = db.query(ClienteDB).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Nome", "CPF", "Telefone", "Email", "Data Nascimento", "Endereco", "Data Cadastro"])
    for c in clientes:
        writer.writerow([c.id, _sanitizar_csv(c.nome), _sanitizar_csv(c.cpf), _sanitizar_csv(c.telefone), _sanitizar_csv(c.email), c.data_nascimento, _sanitizar_csv(c.endereco), c.data_cadastro])
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=clientes.csv"},
    )


@router.get("/exportar/relatorio")
def exportar_relatorio_csv(
    db: Session = Depends(get_db),
    usuario: UsuarioDB = Depends(get_current_user),
):
    clientes = db.query(ClienteDB).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Cliente", "CPF", "Qtd Serviços", "Serviços Pendentes",
        "Valor Serviços (R$)", "Valor Recebido (R$)", "Valor a Receber (R$)",
        "Qtd Empréstimos", "Empréstimos Pendentes", "Total Empréstimos (R$)"
    ])
    for c in clientes:
        qtd_serv = len(c.servicos)
        serv_pend = sum(1 for s in c.servicos if s.status == "Pendente")
        val_serv = sum(s.valor_cobrado for s in c.servicos if s.valor_cobrado)
        val_receb = sum(s.valor_cobrado for s in c.servicos if s.pago and s.valor_cobrado)
        val_pend = val_serv - val_receb
        qtd_emp = len(c.emprestimos)
        emp_pend = sum(1 for e in c.emprestimos if e.status == "Pendente")
        total_emp = sum(e.valor for e in c.emprestimos if e.valor)
        writer.writerow([_sanitizar_csv(c.nome), _sanitizar_csv(c.cpf), qtd_serv, serv_pend,
                         f"{val_serv:.2f}", f"{val_receb:.2f}", f"{val_pend:.2f}",
                         qtd_emp, emp_pend, f"{total_emp:.2f}"])
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=relatorio_geral.csv"},
    )


@router.get("/exportar/receita-csv")
def exportar_receita_csv(
    db: Session = Depends(get_db),
    usuario: UsuarioDB = Depends(get_current_user),
):
    servicos = db.query(ServicoDB).filter(ServicoDB.valor_cobrado > 0).order_by(ServicoDB.data_cadastro.desc()).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Cliente", "Tipo", "Valor", "Pago", "Status", "Data"])
    for s in servicos:
        nome_cliente = _sanitizar_csv(s.cliente.nome if s.cliente else "-")
        writer.writerow([s.id, nome_cliente, s.tipo_servico,
                         f"{s.valor_cobrado:.2f}", "Sim" if s.pago else "Não",
                         s.status, s.data_cadastro.strftime("%d/%m/%Y") if s.data_cadastro else ""])
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=receita_servicos.csv"},
    )
