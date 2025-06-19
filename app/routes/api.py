from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from app.models import Setor, Indicador, ValorIndicador, Dashboard, UsuarioSetor
from app.utils import formatar_valor
from datetime import datetime, timedelta

api_bp = Blueprint('api', __name__)

@api_bp.route('/indicadores/<int:setor_id>')
@login_required
def indicadores_setor(setor_id):
    """API: Obter indicadores de um setor"""
    # Verificar acesso
    if not current_user.admin:
        acesso = UsuarioSetor.query.filter_by(
            usuario_id=current_user.id,
            setor_id=setor_id,
            ativo=True
        ).first()
        if not acesso:
            return jsonify({'error': 'Acesso negado'}), 403
    
    setor = Setor.query.get_or_404(setor_id)
    indicadores = setor.get_indicadores_ativos()
    
    dados = []
    for ind in indicadores:
        valor_atual = ind.get_valor_atual()
        dados.append({
            'id': ind.id,
            'nome': ind.nome,
            'tipo': ind.tipo,
            'unidade': ind.unidade,
            'valor_atual': valor_atual.valor if valor_atual else None,
            'valor_formatado': formatar_valor(
                valor_atual.valor if valor_atual else None, 
                ind.tipo, 
                ind.unidade
            ),
            'meta': ind.meta,
            'status': ind.calcular_status(),
            'cor': ind.cor,
            'icone': ind.icone
        })
    
    return jsonify(dados)

@api_bp.route('/indicador/<int:indicador_id>/historico')
@login_required
def historico_indicador(indicador_id):
    """API: Histórico de um indicador"""
    indicador = Indicador.query.get_or_404(indicador_id)
    
    # Verificar acesso
    if not current_user.admin:
        acesso = UsuarioSetor.query.filter_by(
            usuario_id=current_user.id,
            setor_id=indicador.setor_id,
            ativo=True
        ).first()
        if not acesso:
            return jsonify({'error': 'Acesso negado'}), 403
    
    dias = int(request.args.get('dias', 30))
    valores = indicador.get_valores_periodo(dias)
    
    dados = {
        'indicador': {
            'id': indicador.id,
            'nome': indicador.nome,
            'tipo': indicador.tipo,
            'unidade': indicador.unidade
        },
        'valores': [
            {
                'data': v.data.strftime('%Y-%m-%d'),
                'valor': v.valor,
                'valor_formatado': formatar_valor(v.valor, indicador.tipo, indicador.unidade)
            }
            for v in valores
        ]
    }
    
    return jsonify(dados)

@api_bp.route('/dashboard/<int:setor_id>/salvar', methods=['POST'])
@login_required
def salvar_dashboard(setor_id):
    """API: Salvar configuração do dashboard"""
    # Verificar permissão
    if not current_user.admin:
        acesso = UsuarioSetor.query.filter_by(
            usuario_id=current_user.id,
            setor_id=setor_id,
            ativo=True
        ).first()
        if not acesso or acesso.permissao == 'visualizar':
            return jsonify({'error': 'Sem permissão'}), 403
    
    try:
        configuracao = request.get_json()
        setor = Setor.query.get_or_404(setor_id)
        
        # Buscar dashboard principal ou criar novo
        dashboard = setor.get_dashboard_principal()
        if not dashboard:
            dashboard = Dashboard(
                nome=f'Dashboard {setor.nome}',
                setor_id=setor_id,
                principal=True
            )
            from app import db
            db.session.add(dashboard)
        
        dashboard.set_configuracao(configuracao)
        db.session.commit()
        
        return jsonify({'success': True})
        
    except Exception as e:
        from app import db
        db.session.rollback()
        return jsonify({'error': 'Erro ao salvar dashboard'}), 500
