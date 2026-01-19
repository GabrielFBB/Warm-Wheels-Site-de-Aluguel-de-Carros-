#!/usr/bin/env python3
"""
Script para atualizar a base de dados com as novas funcionalidades:
- Categorias de clientes
- Sistema de pagamento
- Contratos
"""

import os
from flask import Flask
from models import db, User, Payment, PaymentMethod
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

def update_database():
    with app.app_context():
        print("🔄 Atualizando base de dados...")
        
        try:
            # Criar todas as tabelas (incluindo as novas)
            db.create_all()
            print("✅ Tabelas criadas/atualizadas com sucesso!")
            
            # Atualizar usuários existentes com valores padrão
            users = User.query.all()
            updated_users = 0
            
            for user in users:
                if not hasattr(user, 'client_category') or user.client_category is None:
                    user.client_category = 'Económico'
                    user.max_budget = 50.0
                    db.session.add(user)
                    updated_users += 1
            
            if updated_users > 0:
                db.session.commit()
                print(f"✅ {updated_users} utilizadores atualizados com categorias padrão")
            
            # Verificar se existem métodos de pagamento
            payment_methods = PaymentMethod.query.all()
            if not payment_methods:
                print("📝 Adicionando métodos de pagamento...")
                
                methods = [
                    'Cartão de Crédito',
                    'Cartão de Débito', 
                    'PayPal',
                    'Transferência Bancária',
                    'MB Way'
                ]
                
                for method_name in methods:
                    method = PaymentMethod(name=method_name)
                    db.session.add(method)
                
                db.session.commit()
                print("✅ Métodos de pagamento adicionados!")
            
            print("\n🎉 Base de dados atualizada com sucesso!")
            print("\n📊 Resumo das funcionalidades implementadas:")
            print("   • Sistema de categorias de clientes (Gold, Silver, Económico)")
            print("   • Filtro automático de veículos por categoria")
            print("   • Sistema de pagamento completo")
            print("   • Agendamento de recolha de veículos")
            print("   • Contratos de aluguer com preço total")
            print("   • Interface melhorada para gestão de reservas")
            
        except Exception as e:
            print(f"❌ Erro ao atualizar base de dados: {e}")
            db.session.rollback()

if __name__ == '__main__':
    update_database()
