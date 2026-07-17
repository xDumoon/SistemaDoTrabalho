from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Boolean, Text
from sqlalchemy.orm import relationship
from app.database import Base


class UsuarioDB(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    nome = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="user")
    ativo = Column(Boolean, default=True)
    data_cadastro = Column(DateTime, default=datetime.utcnow)


class ClienteDB(Base):
    __tablename__ = "clientes"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True, index=True)
    nome = Column(String, index=True)
    cpf = Column(String, unique=True, index=True)
    telefone = Column(String)
    email = Column(String, nullable=True)
    data_nascimento = Column(String, nullable=True)
    endereco = Column(String, nullable=True)
    observacoes = Column(Text, nullable=True)
    data_cadastro = Column(DateTime, default=datetime.utcnow)

    servicos = relationship("ServicoDB", back_populates="cliente", cascade="all, delete-orphan")
    emprestimos = relationship("EmprestimoDB", back_populates="cliente", cascade="all, delete-orphan")
    usuario = relationship("UsuarioDB", backref="clientes")


class ServicoDB(Base):
    __tablename__ = "servicos_inss"

    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"))
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True, index=True)
    tipo_servico = Column(String)
    status = Column(String, default="Pendente")
    valor_cobrado = Column(Float, default=0.0)
    pago = Column(Boolean, default=False)
    observacoes = Column(Text, nullable=True)
    data_cadastro = Column(DateTime, default=datetime.utcnow)

    cliente = relationship("ClienteDB", back_populates="servicos")
    usuario = relationship("UsuarioDB")


class EmprestimoDB(Base):
    __tablename__ = "emprestimos"

    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"))
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True, index=True)
    valor = Column(Float)
    comissao = Column(Float, default=0.0)
    banco = Column(String)
    parcelas = Column(Integer)
    status = Column(String, default="Pendente")
    data_cadastro = Column(DateTime, default=datetime.utcnow)
    data_conclusao = Column(DateTime, nullable=True)

    cliente = relationship("ClienteDB", back_populates="emprestimos")
    usuario = relationship("UsuarioDB")


class LogDB(Base):
    __tablename__ = "logs"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    usuario_nome = Column(String, nullable=True)
    acao = Column(String)
    entidade = Column(String)
    entidade_id = Column(Integer, nullable=True)
    detalhes = Column(Text, nullable=True)
    data_hora = Column(DateTime, default=datetime.utcnow)


class PedidoAposentadoriaDB(Base):
    __tablename__ = "pedidos_aposentadoria"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True, index=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=False, index=True)
    valor_cobrado = Column(Float, default=0.0)
    pago = Column(Boolean, default=False)
    observacoes = Column(Text, nullable=True)
    status = Column(String, default="Pendente")
    data_cadastro = Column(DateTime, default=datetime.utcnow)
    data_conclusao = Column(DateTime, nullable=True)

    cliente = relationship("ClienteDB")
    usuario = relationship("UsuarioDB")
