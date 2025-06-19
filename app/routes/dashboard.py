from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Setor, Indicador, Dashboard, Usuario, UsuarioSetor
from app.utils import admin_required
from datetime import datetime, timedelta

dashboard_bp = Blueprint('dashboard', __name__, template_folder='../../templates')
setores_bp = Blueprint('setores', __name__, template_folder='../../templates')

@dashboard_bp.route('/')
@login_required
def home():
    """Dashboard principal"""
    # Obter setores do usuário
    if current_user.admin:
        setores = Setor.query.filter_by(ativo=True).all()
    else:
        setores = current_user.get_setores()
    
    # Se usuário tem apenas um setor, redirecionar direto
    if len(setores) == 1:
        return redirect(url_for('dashboard.setor', setor_id=setores[0].id))
    
    # Estatísticas gerais
    stats = {
        'total_setores': len(setores),
        'total_indicadores': sum(len(s.get_indicadores_ativos()) for s in setores),
        'indicadores_ok': 0,
        'indicadores_alerta': 0
    }
    
    # Calcular status dos indicadores
    for setor in setores:
        for indicador in setor.get_indicadores_ativos():
            status = indicador.calcular_status()
            if status == 'positivo':
                stats['indicadores_ok'] += 1
            elif status == 'negativo':
                stats['indicadores_alerta'] += 1
    
    return render_template('dashboard/home.html', setores=setores, stats=stats)

@dashboard_bp.route('/setor/<int:setor_id>')
@login_required
def setor(setor_id):
    """Dashboard de um setor específico"""
    setor = Setor.query.get_or_404(setor_id)
    
    # Verificar acesso ao setor (se não for admin)
    if not current_user.admin:
        acesso = UsuarioSetor.query.filter_by(
            usuario_id=current_user.id,
            setor_id=setor_id,
            ativo=True
        ).first()
        if not acesso:
            flash('Acesso negado a este setor.', 'error')
            return redirect(url_for('dashboard.home'))
    
    # Obter indicadores do setor
    indicadores = setor.get_indicadores_ativos()
    
    # Calcular estatísticas do setor
    stats = {
        'total_indicadores': len(indicadores),
        'indicadores_ok': len([i for i in indicadores if i.calcular_status() == 'positivo']),
        'indicadores_alerta': len([i for i in indicadores if i.calcular_status() == 'negativo']),
        'indicadores_neutro': len([i for i in indicadores if i.calcular_status() == 'neutro'])
    }
    
    return render_template('dashboard/setor.html', 
                         setor=setor, 
                         indicadores=indicadores,
                         stats=stats)



@dashboard_bp.route('/builder/<int:setor_id>')
@login_required
def builder(setor_id):
    """Construtor de dashboard"""
    setor = Setor.query.get_or_404(setor_id)
    
    # Verificar permissão de edição
    if not current_user.admin:
        acesso = UsuarioSetor.query.filter_by(
            usuario_id=current_user.id,
            setor_id=setor_id,
            ativo=True
        ).first()
        if not acesso or acesso.permissao == 'visualizar':
            flash('Sem permissão para editar este dashboard.', 'error')
            return redirect(url_for('dashboard.setor', setor_id=setor_id))
    
    indicadores = setor.get_indicadores_ativos()
    dashboard_config = setor.get_dashboard_principal()
    
    return render_template('dashboard/builder.html', 
                         setor=setor, 
                         indicadores=indicadores,
                         dashboard=dashboard_config)

@setores_bp.route('/setores')
@admin_required
@login_required
def listar_setores():
    """Gerenciar setores (apenas admin)"""
    setores = Setor.query.all()
    return render_template('dashboard/setor.html', setores=setores)
