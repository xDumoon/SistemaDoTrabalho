# Credmax - Sistema de Gestao

Sistema web completo para gestao de escritorio de correspondente bancario e assessoria INSS. Desenvolvido para controle de clientes, servicos, emprestimos, comissoes e relatorios financeiros.

## Funcionalidades

- **Dashboard** com metricas em tempo real (receita, comissao, pendencias)
- **Cadastro de clientes** com validacao de CPF (digitos verificadores)
- **Servicos INSS** com controle de status e pagamentos
- **Emprestimos** com rastreamento de comissao por banco
- **Relatorios financeiros** com exportacao CSV e PDF com graficos
- **Modo escuro** com persistencia de preferencia
- **Auditoria** completa de todas as acoes do sistema
- **Gerenciamento de usuarios** com perfis administrador e usuario
- **Interface responsiva** funcionando em desktop e mobile

## Arquitetura

```
SistemaDoTrabalho/
├── main.py                    # Entry point (uvicorn)
├── app/
│   ├── app.py                 # FastAPI application setup
│   ├── auth.py                # Autenticacao e seguranca
│   ├── models.py              # SQLAlchemy ORM (5 tabelas)
│   ├── schemas.py             # Validacao de dados
│   ├── database.py            # Conexao com banco
│   ├── migrate.py             # Migracoes automaticas
│   ├── routers/
│   │   ├── auth_router.py     # Login e gerenciamento de usuarios
│   │   ├── clientes.py        # CRUD de clientes
│   │   ├── servicos.py        # Servicos INSS
│   │   ├── emprestimos.py     # Emprestimos e comissoes
│   │   └── dashboard.py       # Dashboard e relatorios
│   └── static/
│       ├── index.html         # Frontend SPA completo
│       └── favicon.svg        # Logo Credmax
├── Dockerfile                 # Containerizacao
├── requirements.txt           # Dependencias Python
└── .env.example               # Template de configuracao
```

## Stack Tecnologica

| Camada | Tecnologia |
|--------|-----------|
| Backend | Python 3.12, FastAPI, SQLAlchemy |
| Frontend | HTML5, CSS3, JavaScript vanilla, Bootstrap 5, Chart.js |
| Banco | PostgreSQL (producao) / SQLite (desenvolvimento) |
| Seguranca | Autenticacao JWT, hash de senhas, protecao contra ataques |
| Infra | Docker, Render (cloud), Git/GitHub |

## Como Rodar

### Localmente

```bash
# 1. Clonar o repositorio
git clone https://github.com/xDumoon/SistemaDoTrabalho.git
cd SistemaDoTrabalho

# 2. Criar ambiente virtual
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Copiar arquivo de configuracao
copy .env.example .env  # Windows
# cp .env.example .env  # Linux/Mac

# 5. Rodar
python main.py
```

Acesse: http://127.0.0.1:8000

### Credenciais

| Usuario | Senha | Perfil |
|---------|-------|--------|
| admin | admin123 | Administrador |

> Apos o primeiro login, crie seus proprios usuarios na pagina "Usuarios".

### Configuracao

Para configurar o sistema, edite o arquivo `.env`:

| Variavel | Padrao | Descricao |
|----------|--------|-----------|
| `SECRET_KEY` | (obrigatorio) | Chave para tokens JWT |
| `ADMIN_PASSWORD` | admin123 | Senha do usuario admin |
| `DATABASE_URL` | SQLite local | URL do banco de dados |
| `PORT` | 8000 | Porta do servidor |

### Com Docker

```bash
docker build -t credmax .
docker run -p 8000:8000 -e SECRET_KEY=sua_chave credmax
```

### Deploy na Render (gratuito)

1. Criar conta em https://render.com
2. Criar PostgreSQL Database (free tier)
3. Criar Web Service conectado ao GitHub
4. Configurar variaveis de ambiente:
   - `SECRET_KEY` = chave segura (gerere com `python -c "import secrets; print(secrets.token_hex(32))"`)
   - `ADMIN_PASSWORD` = senha forte para o admin
   - `DATABASE_URL` = URL do PostgreSQL
5. Deploy automatico

> **Importante**: Em producao, sempre defina `ADMIN_PASSWORD` e `SECRET_KEY` seguros.

## Seguranca

- **SECRET_KEY** obrigatoria via variavel de ambiente
- **ADMIN_PASSWORD** configuravel para cada ambiente
- **Rate limit** contra brute force
- **Senhas** protegidas com hash unidirecional
- **Tokens JWT** com expiracao configuravel
- **Validacao** de dados de entrada em todas as camadas
- **Protecao** contra XSS e injecao de dados
- **CORS** configuravel via variavel de ambiente
- **Auditoria** de todas as acoes realizadas no sistema

## Controle Financeiro

- Receita de servicos separada de comissao de emprestimos
- Rastreamento de pagamentos (pago/pendente)
- Dashboard com metricas do mes e total
- Exportacao de relatorios em CSV e PDF com graficos

## Autor

**xDumoon** - Engenharia de Software
