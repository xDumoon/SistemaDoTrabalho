from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class UsuarioCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    nome: str = Field(..., min_length=1, max_length=200)
    password: str = Field(..., min_length=4, max_length=100)
    role: str = Field(default="user", pattern="^(admin|user)$")


class UsuarioResponse(BaseModel):
    id: int
    username: str
    nome: str
    role: str
    ativo: bool
    data_cadastro: datetime

    model_config = {"from_attributes": True}


class LoginRequest(BaseModel):
    username: str = Field(..., max_length=50)
    password: str = Field(..., max_length=100)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    usuario: UsuarioResponse


class ClienteCreate(BaseModel):
    nome: str = Field(..., min_length=1, max_length=200)
    cpf: str = Field(..., min_length=11, max_length=14)
    telefone: str | None = Field(None, max_length=20)
    email: str | None = Field(None, max_length=200)
    data_nascimento: str | None = Field(None, max_length=10)
    endereco: str | None = Field(None, max_length=500)
    observacoes: str | None = Field(None, max_length=2000)

    @field_validator("cpf")
    @classmethod
    def validar_cpf(cls, cpf: str) -> str:
        cpf = cpf.replace(".", "").replace("-", "").strip()
        if not cpf.isdigit() or len(cpf) != 11:
            raise ValueError("CPF deve ter 11 dígitos numéricos")
        if all(d == cpf[0] for d in cpf):
            raise ValueError("CPF inválido: todos os dígitos iguais")
        for j in range(9, 11):
            soma = sum(int(cpf[i]) * (j + 1 - i) for i in range(j))
            digito = (soma * 10 % 11) % 11
            if digito == 10:
                digito = 0
            if int(cpf[j]) != digito:
                raise ValueError("CPF inválido: dígitos verificadores não conferem")
        return cpf


class ClienteUpdate(BaseModel):
    nome: str | None = Field(None, max_length=200)
    telefone: str | None = Field(None, max_length=20)
    email: str | None = Field(None, max_length=200)
    data_nascimento: str | None = Field(None, max_length=10)
    endereco: str | None = Field(None, max_length=500)
    observacoes: str | None = Field(None, max_length=2000)


class ClienteResponse(BaseModel):
    id: int
    nome: str
    cpf: str
    telefone: str
    email: str | None
    data_nascimento: str | None
    endereco: str | None
    observacoes: str | None
    data_cadastro: datetime | None

    model_config = {"from_attributes": True}


class ServicoCreate(BaseModel):
    cliente_id: int
    tipo_servico: str = Field(..., min_length=1, max_length=100)
    valor_cobrado: float = Field(default=0.0, ge=0)
    pago: bool = False
    observacoes: str | None = Field(None, max_length=2000)


class ServicoUpdate(BaseModel):
    tipo_servico: str | None = Field(None, min_length=1, max_length=100)
    valor_cobrado: float | None = Field(None, ge=0)
    pago: bool | None = None
    status: str | None = None
    observacoes: str | None = Field(None, max_length=2000)


class ServicoResponse(BaseModel):
    id: int
    cliente_id: int
    tipo_servico: str
    status: str
    valor_cobrado: float
    pago: bool
    observacoes: str | None
    data_cadastro: datetime | None

    model_config = {"from_attributes": True}


class EmprestimoCreate(BaseModel):
    cliente_id: int
    valor: float = Field(..., gt=0)
    comissao: float = Field(default=0.0, ge=0)
    banco: str = Field(..., min_length=1, max_length=100)
    parcelas: int = Field(..., ge=1, le=480)


class EmprestimoUpdate(BaseModel):
    valor: float | None = Field(None, gt=0)
    comissao: float | None = Field(None, ge=0)
    banco: str | None = Field(None, min_length=1, max_length=100)
    parcelas: int | None = Field(None, ge=1, le=480)
    status: str | None = None


class EmprestimoResponse(BaseModel):
    id: int
    cliente_id: int
    valor: float
    comissao: float
    banco: str
    parcelas: int
    status: str
    data_cadastro: datetime | None
    data_conclusao: datetime | None

    model_config = {"from_attributes": True}


class HistoricoResponse(BaseModel):
    cliente_nome: str
    cpf: str
    telefone: str
    servicos: list[ServicoResponse]
    emprestimos: list[EmprestimoResponse]


class DashboardResponse(BaseModel):
    total_clientes: int
    servicos_pendentes: int
    emprestimos_pendentes: int
    pendencias_totais: int
    total_emprestimos: float
    total_emprestimos_mes: float
    emprestimos_concluidos: int
    comissao_total: float
    comissao_mes: float
    receita_servicos_mes: float
    receita_servicos_total: float
    servicos_pagos_mes: float
    servicos_a_receber: float
    pedidos_apos_pendentes: int = 0
    pedidos_apos_concluidos: int = 0
    pedidos_apos_recebido_mes: float = 0.0
    pedidos_apos_recebido_total: float = 0.0


class LogResponse(BaseModel):
    id: int
    usuario_nome: str | None
    acao: str
    entidade: str
    entidade_id: int | None
    detalhes: str | None
    data_hora: datetime

    model_config = {"from_attributes": True}


class PedidoAposentadoriaCreate(BaseModel):
    cliente_id: int
    valor_cobrado: float = Field(default=0.0, ge=0)
    pago: bool = False
    observacoes: str | None = Field(None, max_length=2000)


class PedidoAposentadoriaUpdate(BaseModel):
    cliente_id: int | None = None
    valor_cobrado: float | None = Field(None, ge=0)
    pago: bool | None = None
    observacoes: str | None = Field(None, max_length=2000)
    status: str | None = None


class PedidoAposentadoriaResponse(BaseModel):
    id: int
    cliente_id: int
    cliente_nome: str | None = None
    cliente_cpf: str | None = None
    cliente_telefone: str | None = None
    valor_cobrado: float
    pago: bool
    observacoes: str | None
    status: str
    data_cadastro: datetime | None
    data_conclusao: datetime | None

    model_config = {"from_attributes": True}
