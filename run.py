from app import create_app, db
from app.models import Usuario, Setor
from flask_migrate import upgrade
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

def criar_usuario_admin():
    """Criar usuário administrador padrão se não existir"""
    try:
        # Verificar se já existe um usuário administrador
        admin_existente = Usuario.query.filter_by(admin=True).first()
        
        if not admin_existente:
            print("Criando usuário administrador padrão...")
            
            # Criar usuário administrador
            admin = Usuario(
                nome='Administrador',
                email='admin@empresa.com',
                admin=True,
                ativo=True
            )
            admin.set_password('123456')
            
            db.session.add(admin)
            
            # Criar setor de exemplo se não existir
            setor_exemplo = Setor.query.filter_by(nome='Vendas').first()
            if not setor_exemplo:
                setor_exemplo = Setor(
                    nome='Vendas',
                    descricao='Setor de vendas da empresa',
                    cor='#007bff'
                )
                db.session.add(setor_exemplo)
            
            db.session.commit()
            
            print("✅ Usuário administrador criado com sucesso!")
            print("📧 Email: admin@empresa.com")
            print("🔑 Senha: 123456")
            print("⚠️  IMPORTANTE: Altere a senha após o primeiro login!")
        else:
            print("ℹ️  Usuário administrador já existe no sistema.")
            
    except Exception as e:
        print(f"❌ Erro ao criar usuário administrador: {e}")
        db.session.rollback()

def inicializar_sistema():
    """Inicializar sistema e banco de dados"""
    with app.app_context():
        # Criar tabelas se não existirem
        db.create_all()
        print("📊 Banco de dados inicializado.")
        
        # Criar usuário administrador se necessário
        criar_usuario_admin()

app = create_app()

if __name__ == '__main__':
    # Inicializar sistema
    inicializar_sistema()
    
    print("🚀 Iniciando servidor Flask...")
    print("🌐 Acesse: http://localhost:5000")
    
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5000)),
        debug=True
    )
