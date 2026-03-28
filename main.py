from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, Session, relationship 

# Inicialização da API
app = FastAPI(title="Sistema INSS e Empréstimos")

# CONFIGURAÇÃO DE SEGURANÇA (CORS)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Permite que qualquer HTML acesse a API (bom para desenvolvimento)
    allow_credentials=True,
    allow_methods=["*"], # Permite GET, POST, etc.
    allow_headers=["*"],
)

URL_BANCO = "sqlite:///./sistema_trabalho.db"
# O check_same_thread=False é necessário apenas para o SQLite funcionar bem com o FastAPI
engine = create_engine(URL_BANCO, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 2. MODELO DA TABELA NO BANCO DE DADOS

class ClienteDB(Base):
    __tablename__ = "clientes"
    
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, index=True)
    cpf = Column(String, unique=True, index=True)
    telefone = Column(String)

    # cria uma ponte invisível no Python para achar os serviços de um cliente fácil
    servicos = relationship("ServicoDB", back_populates="cliente")
    emprestimos = relationship("EmprestimoDB", back_populates="cliente")

class ServicoDB(Base):
    __tablename__ = "servicos_inss"
    
    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id")) # Chave Estrangeira ligando ao cliente
    tipo_servico = Column(String) # Ex: Senha Gov, Requerimento
    status = Column(String, default="Pendente") # Pendente ou Concluído
    observacoes = Column(String, nullable=True) # Campo opcional
    
    cliente = relationship("ClienteDB", back_populates="servicos")

class EmprestimoDB(Base):
    __tablename__ = "emprestimos"
    
    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"))
    valor = Column(Float)
    banco = Column(String)
    parcelas = Column(Integer)
    
    cliente = relationship("ClienteDB", back_populates="emprestimos")

# Comando para criar as tabelas novas automaticamente no arquivo .db

Base.metadata.create_all(bind=engine)

# 3. MODELO DE VALIDAÇÃO (O que o usuário enviará)

# Usando o BaseModel (Pydantic) para o FastAPI validar os dados antes de salvar
class ClienteCreate(BaseModel):
    nome: str
    cpf: str
    telefone: str

# Função auxiliar para abrir e fechar a conexão com o banco a cada requisição
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/clientes/")
def cadastrar_cliente(cliente: ClienteCreate, db: Session = Depends(get_db)):
    # Pega os dados validados e transforma no formato do Banco de Dados
    novo_cliente = ClienteDB(nome=cliente.nome, cpf=cliente.cpf, telefone=cliente.telefone)
    db.add(novo_cliente) # Adiciona
    db.commit()          # Salva (faz o commit)
    db.refresh(novo_cliente) # Atualiza com o ID gerado pelo banco
    return novo_cliente

@app.get("/clientes/")
def listar_clientes(db: Session = Depends(get_db)):
    # Faz um SELECT * FROM clientes
    clientes = db.query(ClienteDB).all()
    return clientes