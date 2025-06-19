from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Setor, Indicador, UsuarioSetor
from app.utils import admin_required
from datetime import datetime

# Criar blueprint para setores
setores_bp = Blueprint('setores', __name__, template_folder='../../templates')

@setores_bp.route('/setores')
@admin_required
@login_required
def listar_setores():
    """Listar todos os setores (apenas admin)"""
    setores = Setor.query.all()
    
    # Calcular estatísticas para cada setor
    for setor in setores:
        setor.total_indicadores = setor.indicadores.count()
        setor.indicadores_ativos = setor.get_indicadores_ativos()
        setor.total_usuarios = setor.usuarios.filter_by(ativo=True).count()
    
    return render_template('setores/lista.html', setores=setores)

@setores_bp.route('/setores/criar', methods=['POST'])
@admin_required
@login_required
def criar_setor():
    """Criar novo setor"""
    nome = request.form.get('nome', '').strip()
    descricao = request.form.get('descricao', '').strip()
    cor = request.form.get('cor', '#007bff')
    
    # Validações
    if not nome:
        flash('Nome do setor é obrigatório.', 'error')
        return redirect(url_for('setores.listar_setores'))
    
    # Verificar se já existe setor com mesmo nome
    if Setor.query.filter_by(nome=nome).first():
        flash('Já existe um setor com este nome.', 'error')
        return redirect(url_for('setores.listar_setores'))
    
    try:
        # Criar setor
        setor = Setor(
            nome=nome,
            descricao=descricao,
            cor=cor,
            ativo=True
        )
        
        db.session.add(setor)
        db.session.commit()
        
        flash(f'Setor "{nome}" criado com sucesso!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash('Erro ao criar setor. Tente novamente.', 'error')
    
    return redirect(url_for('setores.listar_setores'))

@setores_bp.route('/setores/<int:setor_id>/editar', methods=['POST'])
@admin_required
@login_required
def editar_setor(setor_id):
    """Editar setor existente"""
    setor = Setor.query.get_or_404(setor_id)
    
    nome = request.form.get('nome', '').strip()
    descricao = request.form.get('descricao', '').strip()
    cor = request.form.get('cor', '#007bff')
    
    # Validações
    if not nome:
        flash('Nome do setor é obrigatório.', 'error')
        return redirect(url_for('setores.listar_setores'))
    
    # Verificar se já existe outro setor com mesmo nome
    setor_existente = Setor.query.filter_by(nome=nome).first()
    if setor_existente and setor_existente.id != setor_id:
        flash('Já existe um setor com este nome.', 'error')
        return redirect(url_for('setores.listar_setores'))
    
    try:
        # Atualizar setor
        setor.nome = nome
        setor.descricao = descricao
        setor.cor = cor
        
        db.session.commit()
        
        flash(f'Setor "{nome}" atualizado com sucesso!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash('Erro ao atualizar setor. Tente novamente.', 'error')
    
    return redirect(url_for('setores.listar_setores'))

@setores_bp.route('/setores/<int:setor_id>/status', methods=['POST'])
@admin_required
@login_required
def alterar_status_setor(setor_id):
    """Alterar status do setor (ativar/desativar)"""
    setor = Setor.query.get_or_404(setor_id)
    
    try:
        # Verificar se há indicadores ativos antes de desativar
        if setor.ativo and setor.get_indicadores_ativos():
            return jsonify({
                'error': 'Não é possível desativar setor com indicadores ativos'
            }), 400
        
        setor.ativo = not setor.ativo
        db.session.commit()
        
        status = 'ativado' if setor.ativo else 'desativado'
        return jsonify({
            'success': True,
            'message': f'Setor {status} com sucesso!',
            'novo_status': setor.ativo
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Erro ao alterar status do setor'}), 500

@setores_bp.route('/setores/<int:setor_id>/usuarios')
@admin_required
@login_required
def usuarios_setor(setor_id):
    """Listar usuários do setor"""
    setor = Setor.query.get_or_404(setor_id)
    usuarios_setor = UsuarioSetor.query.filter_by(setor_id=setor_id, ativo=True).all()
    
    return jsonify({
        'setor': {
            'id': setor.id,
            'nome': setor.nome
        },
        'usuarios': [
            {
                'id': us.usuario.id,
                'nome': us.usuario.nome,
                'email': us.usuario.email,
                'permissao': us.permissao
            }
            for us in usuarios_setor
        ]
    })

@setores_bp.route('/setores/<int:setor_id>/estatisticas')
@admin_required
@login_required
def estatisticas_setor(setor_id):
    """Obter estatísticas do setor"""
    setor = Setor.query.get_or_404(setor_id)
    
    # Calcular estatísticas
    total_indicadores = setor.indicadores.count()
    indicadores_ativos = len(setor.get_indicadores_ativos())
    total_usuarios = setor.usuarios.filter_by(ativo=True).count()
    
    # Status dos indicadores
    indicadores_positivos = 0
    indicadores_negativos = 0
    indicadores_neutros = 0
    
    for indicador in setor.get_indicadores_ativos():
        status = indicador.calcular_status()
        if status == 'positivo':
            indicadores_positivos += 1
        elif status == 'negativo':
            indicadores_negativos += 1
        else:
            indicadores_neutros += 1
    
    return jsonify({
        'setor': {
            'id': setor.id,
            'nome': setor.nome,
            'descricao': setor.descricao,
            'cor': setor.cor
        },
        'estatisticas': {
            'total_indicadores': total_indicadores,
            'indicadores_ativos': indicadores_ativos,
            'total_usuarios': total_usuarios,
            'indicadores_positivos': indicadores_positivos,
            'indicadores_negativos': indicadores_negativos,
            'indicadores_neutros': indicadores_neutros
        }
    })

@setores_bp.route('/setores/<int:setor_id>/excluir', methods=['POST'])
@admin_required
@login_required
def excluir_setor(setor_id):
    """Excluir setor (apenas se não tiver indicadores)"""
    setor = Setor.query.get_or_404(setor_id)
    
    try:
        # Verificar se há indicadores associados
        if setor.indicadores.count() > 0:
            return jsonify({
                'error': 'Não é possível excluir setor com indicadores associados'
            }), 400
        
        # Verificar se há usuários associados
        if setor.usuarios.count() > 0:
            return jsonify({
                'error': 'Não é possível excluir setor com usuários associados'
            }), 400
        
        nome_setor = setor.nome
        db.session.delete(setor)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Setor "{nome_setor}" excluído com sucesso!'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Erro ao excluir setor'}), 500

@setores_bp.route('/setores/novo', methods=['GET'])
@admin_required
@login_required
def novo_setor():
    """Formulário para novo setor"""
    return render_template('setores/setor.html')

@setores_bp.route('/setores/<int:setor_id>/editar', methods=['GET'])
@admin_required
@login_required
def edit_setor(setor_id):
    """Formulário para editar setor"""
    setor = Setor.query.get_or_404(setor_id)
    return render_template('setores/setor.html', setor=setor)
