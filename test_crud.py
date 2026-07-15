import sys
sys.path.insert(0, 'C:\\sistemadotrabalho\\SistemaDoTrabalho')
from dotenv import load_dotenv
load_dotenv()
from fastapi.testclient import TestClient
from app.app import app
c = TestClient(app)

# Login
r = c.post('/auth/login', json={"username":"admin","password":"admin123"})
token = r.json()["access_token"]
h = {"Authorization": f"Bearer {token}"}

# Limpar dados de teste anteriores
from app.database import SessionLocal
from app.models import ClienteDB
db = SessionLocal()
for cli in db.query(ClienteDB).all():
    db.delete(cli)
db.commit()
db.close()

# Criar cliente - simulate frontend form
payload = {
    "nome": "Joao Teste",
    "cpf": "52998224725",
    "telefone": "11977776666",
    "email": None,
    "data_nascimento": None,
    "endereco": None,
    "observacoes": None
}
print("Payload:", payload)
r = c.post("/clientes/", json=payload, headers=h)
print("Status:", r.status_code)
print("Body:", r.json())

# Listar
r = c.get("/clientes/", headers=h)
print("Total apos criar:", len(r.json()))
for cli in r.json():
    print(f"  - {cli['nome']} ({cli['cpf']})")

# Servico
r = c.post("/servicos/", json={"cliente_id": 1, "tipo_servico": "Desbloqueio", "valor_cobrado": 150.0, "pago": False}, headers=h)
print("Servico status:", r.status_code)

# Emprestimo
r = c.post("/emprestimos/", json={"cliente_id": 1, "valor": 15000.0, "comissao": 750.0, "banco": "Itau", "parcelas": 60}, headers=h)
print("Emprestimo status:", r.status_code)

# Dashboard
r = c.get("/dashboard", headers=h)
d = r.json()
print(f"Dashboard: clientes={d['total_clientes']}, serv_pend={d['servicos_pendentes']}, emp_pend={d['emprestimos_pendentes']}")
