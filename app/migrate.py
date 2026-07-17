from sqlalchemy import inspect, text
from sqlalchemy.exc import OperationalError
from app.database import engine


def executar_migracoes():
    inspector = inspect(engine)

    with engine.connect() as conn:
        # Migração: tabela clientes
        if inspector.has_table("clientes"):
            colunas_clientes = [c["name"] for c in inspector.get_columns("clientes")]
            novas_colunas = {
                "email": "VARCHAR",
                "data_nascimento": "VARCHAR",
                "endereco": "VARCHAR",
                "observacoes": "TEXT",
                "data_cadastro": "TIMESTAMP",
            }
            for col, tipo in novas_colunas.items():
                if col not in colunas_clientes:
                    try:
                        conn.execute(text(f"ALTER TABLE clientes ADD COLUMN {col} {tipo}"))
                    except OperationalError:
                        pass

        # Migração: tabela servicos_inss
        if inspector.has_table("servicos_inss"):
            colunas_servicos = [c["name"] for c in inspector.get_columns("servicos_inss")]
            novas_serv = {
                "data_cadastro": "TIMESTAMP",
                "valor_cobrado": "FLOAT DEFAULT 0.0",
                "pago": "BOOLEAN DEFAULT 0",
            }
            for col, tipo in novas_serv.items():
                if col not in colunas_servicos:
                    try:
                        conn.execute(text(f"ALTER TABLE servicos_inss ADD COLUMN {col} {tipo}"))
                    except OperationalError:
                        pass

        # Migração: tabela emprestimos
        if inspector.has_table("emprestimos"):
            colunas_emprestimos = [c["name"] for c in inspector.get_columns("emprestimos")]
            novas_emp = {
                "data_cadastro": "TIMESTAMP",
                "data_conclusao": "TIMESTAMP",
                "comissao": "FLOAT DEFAULT 0.0",
            }
            for col, tipo in novas_emp.items():
                if col not in colunas_emprestimos:
                    try:
                        conn.execute(text(f"ALTER TABLE emprestimos ADD COLUMN {col} {tipo}"))
                    except OperationalError:
                        pass

        if inspector.has_table("clientes"):
            colunas_clientes = [c["name"] for c in inspector.get_columns("clientes")]
            if "usuario_id" not in colunas_clientes:
                try:
                    conn.execute(text("ALTER TABLE clientes ADD COLUMN usuario_id INTEGER REFERENCES usuarios(id)"))
                except OperationalError:
                    pass

        if inspector.has_table("servicos_inss"):
            colunas_servicos = [c["name"] for c in inspector.get_columns("servicos_inss")]
            if "usuario_id" not in colunas_servicos:
                try:
                    conn.execute(text("ALTER TABLE servicos_inss ADD COLUMN usuario_id INTEGER REFERENCES usuarios(id)"))
                except OperationalError:
                    pass

        if inspector.has_table("emprestimos"):
            colunas_emprestimos = [c["name"] for c in inspector.get_columns("emprestimos")]
            if "usuario_id" not in colunas_emprestimos:
                try:
                    conn.execute(text("ALTER TABLE emprestimos ADD COLUMN usuario_id INTEGER REFERENCES usuarios(id)"))
                except OperationalError:
                    pass

        if inspector.has_table("pedidos_aposentadoria"):
            colunas_pos = [c["name"] for c in inspector.get_columns("pedidos_aposentadoria")]
            if "nome_cliente" in colunas_pos or "valor_cobrado" not in colunas_pos:
                try:
                    conn.execute(text("DROP TABLE pedidos_aposentadoria"))
                    conn.commit()
                except OperationalError:
                    pass
                inspector = inspect(engine)

        if not inspector.has_table("pedidos_aposentadoria"):
            try:
                conn.execute(text("""
                    CREATE TABLE pedidos_aposentadoria (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        usuario_id INTEGER REFERENCES usuarios(id),
                        cliente_id INTEGER NOT NULL REFERENCES clientes(id),
                        valor_cobrado FLOAT DEFAULT 0.0,
                        pago BOOLEAN DEFAULT 0,
                        observacoes TEXT,
                        status VARCHAR DEFAULT 'Pendente',
                        data_cadastro TIMESTAMP,
                        data_conclusao TIMESTAMP
                    )
                """))
            except OperationalError:
                pass

        conn.commit()
