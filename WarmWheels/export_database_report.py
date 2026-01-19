#!/usr/bin/env python3
"""
Script para gerar um relatório completo da base de dados
para envio ao curso
"""

import os
import sqlite3
from datetime import datetime

def generate_database_report():
    db_path = 'instance/site.db'
    
    if not os.path.exists(db_path):
        print("❌ Base de dados não encontrada.")
        return
    
    print("📊 Gerando relatório da base de dados...")
    
    try:
        # Conectar à base de dados
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Criar relatório
        report = []
        report.append("# Relatório da Base de Dados WarmWheels")
        report.append(f"**Gerado em:** {datetime.now().strftime('%d/%m/%Y às %H:%M')}")
        report.append("")
        
        # 1. Estrutura das tabelas
        report.append("## 📋 Estrutura das Tabelas")
        report.append("")
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        for table in tables:
            table_name = table[0]
            report.append(f"### Tabela: `{table_name}`")
            
            # Obter colunas
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            report.append("| Coluna | Tipo | Null | Chave |")
            report.append("|--------|------|------|-------|")
            
            for col in columns:
                col_name, col_type, not_null, default, pk = col
                null_text = "Não" if not_null else "Sim"
                pk_text = "Sim" if pk else "Não"
                report.append(f"| {col_name} | {col_type} | {null_text} | {pk_text} |")
            
            report.append("")
        
        # 2. Dados das tabelas
        report.append("## 📊 Dados das Tabelas")
        report.append("")
        
        for table in tables:
            table_name = table[0]
            report.append(f"### Dados da tabela `{table_name}`")
            
            # Contar registos
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            report.append(f"**Total de registos:** {count}")
            
            if count > 0:
                # Obter alguns registos de exemplo
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 5")
                rows = cursor.fetchall()
                
                if rows:
                    # Obter nomes das colunas
                    cursor.execute(f"PRAGMA table_info({table_name})")
                    columns = [col[1] for col in cursor.fetchall()]
                    
                    # Criar tabela de exemplo
                    report.append("**Primeiros 5 registos:**")
                    report.append("")
                    
                    # Cabeçalho da tabela
                    header = "| " + " | ".join(columns) + " |"
                    separator = "|" + "|".join([" --- " for _ in columns]) + "|"
                    report.append(header)
                    report.append(separator)
                    
                    # Dados
                    for row in rows:
                        row_str = "| " + " | ".join([str(cell) if cell is not None else "NULL" for cell in row]) + " |"
                        report.append(row_str)
            
            report.append("")
        
        # 3. Estatísticas gerais
        report.append("## 📈 Estatísticas Gerais")
        report.append("")
        
        # Utilizadores por categoria
        cursor.execute("SELECT client_category, COUNT(*) FROM users GROUP BY client_category")
        categories = cursor.fetchall()
        
        if categories:
            report.append("### Utilizadores por Categoria")
            report.append("| Categoria | Número de Utilizadores |")
            report.append("|-----------|------------------------|")
            for cat, count in categories:
                report.append(f"| {cat} | {count} |")
            report.append("")
        
        # Veículos por categoria
        cursor.execute("SELECT category, COUNT(*) FROM vehicles GROUP BY category")
        vehicle_categories = cursor.fetchall()
        
        if vehicle_categories:
            report.append("### Veículos por Categoria")
            report.append("| Categoria | Número de Veículos |")
            report.append("|-----------|-------------------|")
            for cat, count in vehicle_categories:
                report.append(f"| {cat} | {count} |")
            report.append("")
        
        # Reservas por status
        cursor.execute("SELECT status, COUNT(*) FROM reservations GROUP BY status")
        reservations = cursor.fetchall()
        
        if reservations:
            report.append("### Reservas por Status")
            report.append("| Status | Número de Reservas |")
            report.append("|--------|-------------------|")
            for status, count in reservations:
                report.append(f"| {status} | {count} |")
            report.append("")
        
        # 4. Funcionalidades implementadas
        report.append("## 🚀 Funcionalidades Implementadas")
        report.append("")
        report.append("- ✅ Sistema de categorias de clientes (Gold, Silver, Económico)")
        report.append("- ✅ Filtro automático de veículos por categoria")
        report.append("- ✅ Sistema de pagamento completo")
        report.append("- ✅ Agendamento de recolha de veículos")
        report.append("- ✅ Contratos de aluguer com preço total")
        report.append("- ✅ Interface melhorada para gestão de reservas")
        report.append("- ✅ Gestão de categoria do cliente")
        report.append("- ✅ Sistema de autenticação baseado em categoria")
        report.append("")
        
        # 5. Tecnologias utilizadas
        report.append("## 🛠️ Tecnologias Utilizadas")
        report.append("")
        report.append("- **Backend:** Flask (Python)")
        report.append("- **Base de Dados:** SQLite")
        report.append("- **Frontend:** HTML, CSS, JavaScript")
        report.append("- **Autenticação:** Flask-Login")
        report.append("- **Formulários:** WTForms")
        report.append("- **ORM:** SQLAlchemy")
        report.append("")
        
        # Salvar relatório
        report_content = "\n".join(report)
        
        with open("database_report.md", "w", encoding="utf-8") as f:
            f.write(report_content)
        
        print("✅ Relatório gerado com sucesso!")
        print("📄 Arquivo criado: database_report.md")
        print("\n📋 Conteúdo do relatório:")
        print("   • Estrutura completa das tabelas")
        print("   • Dados de exemplo de cada tabela")
        print("   • Estatísticas gerais")
        print("   • Funcionalidades implementadas")
        print("   • Tecnologias utilizadas")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Erro ao gerar relatório: {e}")

if __name__ == '__main__':
    generate_database_report()
