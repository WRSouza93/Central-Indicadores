from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.urls import url_parse
from app import db
from app.models import Usuario, Setor, UsuarioSetor
from app.utils import admin_required

auth_bp = Blueprint('auth', __name__, template_folder='../../templates')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Página de login"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.home'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        senha = request.form.get('senha')
        lembrar = bool(request.form.get('lembrar'))
        
        if not email or not senha:
            flash('Email e senha são obrigatórios.', 'error')
            return render_template('auth/login.html')
        
        usuario = Usuario.query.filter_by(email=email.lower().strip()).first()
        
        if usuario and usuario.check_password(senha) and usuario.ativo:
            login_user(usuario, remember=lembrar)
            
            # Redirecionar para página solicitada ou dashboard
            next_page = request.args.get('next')
            if not next_page or url_parse(next_page).netloc != '':
                next_page = url_for('dashboard.home')
            
            flash(f'Bem-vindo, {usuario.nome}!', 'success')
            return redirect(next_page)
        else:
            flash('Email ou senha incorretos.', 'error')
    
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """Logout do usuário"""
    nome = current_user.nome
    logout_user()
    flash(f'Até logo, {nome}!', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/usuarios', methods=['GET'])
@admin_required
@login_required
def usuarios():
    """Gerenciar usuários (apenas para admin)"""
    usuarios = Usuario.query.all()
    setores = Setor.query.filter_by(ativo=True).all()
    
    return render_template('auth/usuarios.html', 
                         usuarios=usuarios, 
                         setores=setores)

@auth_bp.route('/usuarios/criar', methods=['POST'])
@admin_required
@login_required
def criar_usuario():
    """Criar novo usuário"""
    nome = request.form.get('nome', '').strip()
    email = request.form.get('email', '').lower().strip()
    senha = request.form.get('senha')
    admin = bool(request.form.get('admin'))
    ativo = bool(request.form.get('ativo', True))
    setores_ids = request.form.getlist('setores')
    
    # Validações
    if not nome or not email or not senha:
        flash('Nome, email e senha são obrigatórios.', 'error')
        return redirect(url_for('auth.usuarios'))
    
    if len(senha) < 6:
        flash('A senha deve ter pelo menos 6 caracteres.', 'error')
        return redirect(url_for('auth.usuarios'))
    
    # Verificar se email já existe
    if Usuario.query.filter_by(email=email).first():
        flash('Este email já está cadastrado.', 'error')
        return redirect(url_for('auth.usuarios'))
    
    try:
        # Criar usuário
        usuario = Usuario(
            nome=nome,
            email=email,
            admin=admin,
            ativo=ativo
        )
        usuario.set_password(senha)
        
        db.session.add(usuario)
        db.session.flush()  # Para obter o ID do usuário
        
        # Associar setores
        for setor_id in setores_ids:
            usuario_setor = UsuarioSetor(
                usuario_id=usuario.id,
                setor_id=int(setor_id),
                permissao='editar',
                ativo=True
            )
            db.session.add(usuario_setor)
        
        db.session.commit()
        flash(f'Usuário "{nome}" criado com sucesso!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash('Erro ao criar usuário. Tente novamente.', 'error')
    
    return redirect(url_for('auth.usuarios'))

@auth_bp.route('/usuarios/<int:usuario_id>/status', methods=['POST'])
@admin_required
@login_required
def alterar_status_usuario(usuario_id):
    """Alterar status do usuário"""
    usuario = Usuario.query.get_or_404(usuario_id)
    
    # Não permitir desativar o último admin
    if usuario.admin and usuario.ativo:
        admins_ativos = Usuario.query.filter_by(admin=True, ativo=True).count()
        if admins_ativos <= 1:
            return jsonify({'error': 'Não é possível desativar o último administrador'}), 400
    
    try:
        usuario.ativo = not usuario.ativo
        db.session.commit()
        
        status = 'ativado' if usuario.ativo else 'desativado'
        return jsonify({
            'success': True, 
            'message': f'Usuário {status} com sucesso!',
            'novo_status': usuario.ativo
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Erro ao alterar status do usuário'}), 500

@auth_bp.route('/perfil', methods=['GET', 'POST'])
@login_required
def perfil():
    """Editar perfil do usuário"""
    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        senha_atual = request.form.get('senha_atual')
        nova_senha = request.form.get('nova_senha')
        confirmar_senha = request.form.get('confirmar_senha')
        
        # Validar nome
        if not nome:
            flash('Nome é obrigatório.', 'error')
            return render_template('auth/perfil.html')
        
        # Atualizar nome
        current_user.nome = nome
        
        # Alterar senha se fornecida
        if nova_senha:
            if not senha_atual or not current_user.check_password(senha_atual):
                flash('Senha atual incorreta.', 'error')
                return render_template('auth/perfil.html')
            
            if len(nova_senha) < 6:
                flash('A nova senha deve ter pelo menos 6 caracteres.', 'error')
                return render_template('auth/perfil.html')
            
            if nova_senha != confirmar_senha:
                flash('Confirmação de senha não confere.', 'error')
                return render_template('auth/perfil.html')
            
            current_user.set_password(nova_senha)
        
        try:
            db.session.commit()
            flash('Perfil atualizado com sucesso!', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Erro ao atualizar perfil.', 'error')
    
    return render_template('auth/perfil.html')
