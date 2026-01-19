#!/usr/bin/env python3
"""
Script de migração para adicionar as novas colunas à base de dados existente
"""

import sqlite3
import os
from datetime import datetime

def migrate_database():
    db_path = 'instance/site.db'
    
    if not os.path.exists(db_path):
        print("❌ Base de dados não encontrada. Execute primeiro o main.py para criar a base de dados.")
        return
    
    print("🔄 Iniciando migração da base de dados...")
    
    try:
        # Conectar à base de dados
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar se as colunas já existem
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Adicionar colunas se não existirem
        if 'client_category' not in columns:
            print("📝 Adicionando coluna client_category...")
            cursor.execute("ALTER TABLE users ADD COLUMN client_category VARCHAR(20) DEFAULT 'Económico'")
        
        if 'max_budget' not in columns:
            print("📝 Adicionando coluna max_budget...")
            cursor.execute("ALTER TABLE users ADD COLUMN max_budget FLOAT DEFAULT 50.0")
        
        # Verificar se a tabela payments existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='payments'")
        if not cursor.fetchone():
            print("📝 Criando tabela payments...")
            cursor.execute("""
                CREATE TABLE payments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    reservation_id INTEGER NOT NULL,
                    amount FLOAT NOT NULL,
                    payment_status VARCHAR(20) DEFAULT 'Pendente',
                    payment_date DATETIME,
                    transaction_id VARCHAR(100) UNIQUE,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (reservation_id) REFERENCES reservations (id)
                )
            """)
        
        # Verificar se as colunas da tabela reservations existem
        cursor.execute("PRAGMA table_info(reservations)")
        res_columns = [column[1] for column in cursor.fetchall()]
        
        if 'status' not in res_columns:
            print("📝 Adicionando coluna status à tabela reservations...")
            cursor.execute("ALTER TABLE reservations ADD COLUMN status VARCHAR(20) DEFAULT 'Pendente'")
        
        if 'pickup_date' not in res_columns:
            print("📝 Adicionando coluna pickup_date à tabela reservations...")
            cursor.execute("ALTER TABLE reservations ADD COLUMN pickup_date DATETIME")
        
        if 'contract_number' not in res_columns:
            print("📝 Adicionando coluna contract_number à tabela reservations...")
            cursor.execute("ALTER TABLE reservations ADD COLUMN contract_number VARCHAR(50)")
        
        # Atualizar reservas existentes
        cursor.execute("UPDATE reservations SET status = 'Pendente' WHERE status IS NULL")
        
        # Adicionar métodos de pagamento se não existirem
        cursor.execute("SELECT COUNT(*) FROM payment_methods")
        if cursor.fetchone()[0] == 0:
            print("📝 Adicionando métodos de pagamento...")
            methods = [
                'Cartão de Crédito',
                'Cartão de Débito', 
                'PayPal',
                'Transferência Bancária',
                'MB Way'
            ]
            
            for method in methods:
                cursor.execute("INSERT INTO payment_methods (name, created_at, updated_at) VALUES (?, ?, ?)",
                             (method, datetime.now(), datetime.now()))
        
        # Commit das alterações
        conn.commit()
        conn.close()
        
        print("✅ Migração concluída com sucesso!")
        print("\n📊 Funcionalidades implementadas:")
        print("   • Sistema de categorias de clientes (Gold, Silver, Económico)")
        print("   • Filtro automático de veículos por categoria")
        print("   • Sistema de pagamento completo")
        print("   • Agendamento de recolha de veículos")
        print("   • Contratos de aluguer com preço total")
        print("   • Interface melhorada para gestão de reservas")
        
    except Exception as e:
        print(f"❌ Erro durante a migração: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()

if __name__ == '__main__':
    migrate_database()
