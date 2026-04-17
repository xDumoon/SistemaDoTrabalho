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
class ServicoCreate(BaseModel):
    cliente_id: int
    tipo_servico: str
    observacoes: str | None = None  # opcional

class EmprestimoCreate(BaseModel):
    cliente_id: int
    valor: float
    banco: str
    parcelas: int

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
    return db.query(ClienteDB).all()

# ROTAS PARA SERVIÇOS INSS

@app.post("/servicos/")
def cadastrar_servico(servico: ServicoCreate, db: Session = Depends(get_db)):
    novo_servico = ServicoDB(**servico.dict()) # Esse atalho pega todos os campos do Pydantic de uma vez
    db.add(novo_servico)
    db.commit()
    db.refresh(novo_servico)
    return novo_servico

@app.get("/clientes/{cliente_id}/servicos/")
def listar_servicos_do_cliente(cliente_id: int, db: Session = Depends(get_db)):
    # Busca apenas os serviços onde o ID do cliente é igual ao que passamos na URL
    return db.query(ServicoDB).filter(ServicoDB.cliente_id == cliente_id).all()

# ROTAS PARA EMPRÉSTIMOS

@app.post("/emprestimos/")
def cadastrar_emprestimo(emprestimo: EmprestimoCreate, db: Session = Depends(get_db)):
    novo_emprestimo = EmprestimoDB(**emprestimo.dict())
    db.add(novo_emprestimo)
    db.commit()
    db.refresh(novo_emprestimo)
    return novo_emprestimo

# ROTA DE HISTÓRICO (O Raio-X do Cliente)

@app.get("/clientes/{cliente_id}/historico")
def ver_historico_cliente(cliente_id: int, db: Session = Depends(get_db)):
    # 1. Busca o cliente pelo ID
    cliente = db.query(ClienteDB).filter(ClienteDB.id == cliente_id).first()
    
    # Se o cliente não existir, devolve um erro amigável
    if not cliente:
        return {"erro": "Cliente não encontrado"}
        
    # 2. Prepara os dados dos serviços para enviar
    servicos_lista = []
    for s in cliente.servicos:
        servicos_lista.append({
            "id": s.id,
            "tipo": s.tipo_servico,
            "status": s.status,
            "observacoes": s.observacoes
        })
        
    # 3. Prepara os dados dos empréstimos
    emprestimos_lista = []
    for e in cliente.emprestimos:
        emprestimos_lista.append({
            "id": e.id,
            "banco": e.banco,
            "valor": e.valor,
            "parcelas": e.parcelas
        })
        
    # 4. Devolve o pacote completo!
    return {
        "cliente_nome": cliente.nome,
        "cpf": cliente.cpf,
        "telefone": cliente.telefone,
        "servicos": servicos_lista,
        "emprestimos": emprestimos_lista
    }
    # ==========================================
    # ROTA PARA ATUALIZAR STATUS DO SERVIÇO (PUT)
    # ==========================================
@app.put("/servicos/{servico_id}/concluir")
def concluir_servico(servico_id: int, db: Session = Depends(get_db)):
    # 1. Procura o serviço no banco de dados
    servico = db.query(ServicoDB).filter(ServicoDB.id == servico_id).first()
    
    # 2. Se não achar, devolve um erro
    if not servico:
        return {"erro": "Serviço não encontrado"}
        
    # 3. Muda o status, salva e atualiza!
    servico.status = "Concluído"
    db.commit()
    db.refresh(servico)
    
    return {"mensagem": "Serviço concluído com sucesso!", "status": servico.status}
# ==========================================
# ROTAS DE EXCLUSÃO (DELETE)
# ==========================================
@app.delete("/servicos/{servico_id}")
def deletar_servico(servico_id: int, db: Session = Depends(get_db)):
    # Acha o serviço
    servico = db.query(ServicoDB).filter(ServicoDB.id == servico_id).first()
    if not servico:
        return {"erro": "Serviço não encontrado"}
    
    # Exclui e salva
    db.delete(servico)
    db.commit()
    return {"mensagem": "Serviço excluído com sucesso!"}

@app.delete("/emprestimos/{emprestimo_id}")
def deletar_emprestimo(emprestimo_id: int, db: Session = Depends(get_db)):
    # Acha o empréstimo
    emprestimo = db.query(EmprestimoDB).filter(EmprestimoDB.id == emprestimo_id).first()
    if not emprestimo:
        return {"erro": "Empréstimo não encontrado"}
    
    # Exclui e salva
    db.delete(emprestimo)
    db.commit()
    return {"mensagem": "Empréstimo excluído com sucesso!"}