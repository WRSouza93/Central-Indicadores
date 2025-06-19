from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Setor, Indicador, ValorIndicador, UsuarioSetor, GraficoIndicador
from app.utils import admin_required, formatar_valor
from datetime import datetime, timedelta
from sqlalchemy import text
import json

indicadores_bp = Blueprint('indicadores', __name__)

@indicadores_bp.route('/')
@login_required
def lista():
    """Lista todos os indicadores do usuário"""
    if current_user.admin:
        indicadores = Indicador.query.filter_by(ativo=True).all()
    else:
        # Obter indicadores dos setores do usuário
        setores_ids = [s.id for s in current_user.get_setores()]
        indicadores = Indicador.query.filter(
            Indicador.setor_id.in_(setores_ids),
            Indicador.ativo == True
        ).all()
    
    return render_template('indicadores/list.html', indicadores=indicadores)

@indicadores_bp.route('/setor/<int:setor_id>')
@login_required
def por_setor(setor_id):
    """Lista indicadores de um setor específico"""
    setor = Setor.query.get_or_404(setor_id)
    
    # Verificar acesso ao setor
    if not current_user.admin:
        acesso = UsuarioSetor.query.filter_by(
            usuario_id=current_user.id,
            setor_id=setor_id,
            ativo=True
        ).first()
        if not acesso:
            flash('Acesso negado a este setor.', 'error')
            return redirect(url_for('indicadores.lista'))
    
    indicadores = setor.get_indicadores_ativos()
    return render_template('indicadores/list.html', 
                         indicadores=indicadores, 
                         setor=setor)

@indicadores_bp.route('/criar/<int:setor_id>', methods=['GET', 'POST'])
@login_required
def criar(setor_id):
    """Criar novo indicador"""
    setor = Setor.query.get_or_404(setor_id)
    
    # Verificar permissão de edição
    if not current_user.admin:
        acesso = UsuarioSetor.query.filter_by(
            usuario_id=current_user.id,
            setor_id=setor_id,
            ativo=True
        ).first()
        if not acesso or acesso.permissao == 'visualizar':
            flash('Sem permissão para criar indicadores neste setor.', 'error')
            return redirect(url_for('indicadores.por_setor', setor_id=setor_id))
    
    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        descricao = request.form.get('descricao', '').strip()
        tipo = request.form.get('tipo')
        unidade = request.form.get('unidade', '').strip()
        meta = request.form.get('meta')
        meta_tipo = request.form.get('meta_tipo', 'maior')
        cor = request.form.get('cor', '#28a745')
        icone = request.form.get('icone', 'fas fa-chart-line')
        
        # Validações
        if not nome or not tipo:
            flash('Nome e tipo são obrigatórios.', 'error')
            return render_template('indicadores/form.html', setor=setor)
        
        # Converter meta para float se fornecida
        meta_valor = None
        if meta:
            try:
                meta_valor = float(meta.replace(',', '.'))
            except ValueError:
                flash('Meta deve ser um número válido.', 'error')
                return render_template('indicadores/form.html', setor=setor)
        
        # Criar indicador
        indicador = Indicador(
            nome=nome,
            descricao=descricao,
            tipo=tipo,
            unidade=unidade,
            meta=meta_valor,
            meta_tipo=meta_tipo,
            cor=cor,
            icone=icone,
            setor_id=setor_id,
            ordem=Indicador.query.filter_by(setor_id=setor_id).count()
        )
        
        try:
            db.session.add(indicador)
            db.session.commit()
            flash(f'Indicador "{nome}" criado com sucesso!', 'success')
            return redirect(url_for('indicadores.por_setor', setor_id=setor_id))
        except Exception as e:
            db.session.rollback()
            flash('Erro ao criar indicador. Tente novamente.', 'error')
    
    return render_template('indicadores/form.html', setor=setor)

@indicadores_bp.route('/editar/<int:indicador_id>', methods=['GET', 'POST'])
@login_required
def editar(indicador_id):
    """Editar indicador existente"""
    indicador = Indicador.query.get_or_404(indicador_id)
    
    # Verificar permissão de edição
    if not current_user.admin:
        acesso = UsuarioSetor.query.filter_by(
            usuario_id=current_user.id,
            setor_id=indicador.setor_id,
            ativo=True
        ).first()
        if not acesso or acesso.permissao == 'visualizar':
            flash('Sem permissão para editar este indicador.', 'error')
            return redirect(url_for('indicadores.por_setor', setor_id=indicador.setor_id))
    
    if request.method == 'POST':
        indicador.nome = request.form.get('nome', '').strip()
        indicador.descricao = request.form.get('descricao', '').strip()
        indicador.tipo = request.form.get('tipo')
        indicador.unidade = request.form.get('unidade', '').strip()
        indicador.meta_tipo = request.form.get('meta_tipo', 'maior')
        indicador.cor = request.form.get('cor', '#28a745')
        indicador.icone = request.form.get('icone', 'fas fa-chart-line')
        
        # Converter meta
        meta = request.form.get('meta')
        if meta:
            try:
                indicador.meta = float(meta.replace(',', '.'))
            except ValueError:
                flash('Meta deve ser um número válido.', 'error')
                return render_template('indicadores/form.html', 
                                     indicador=indicador, 
                                     setor=indicador.setor)
        else:
            indicador.meta = None
        
        # Validações
        if not indicador.nome or not indicador.tipo:
            flash('Nome e tipo são obrigatórios.', 'error')
            return render_template('indicadores/form.html', 
                                 indicador=indicador, 
                                 setor=indicador.setor)
        
        try:
            db.session.commit()
            flash(f'Indicador "{indicador.nome}" atualizado com sucesso!', 'success')
            return redirect(url_for('indicadores.por_setor', setor_id=indicador.setor_id))
        except Exception as e:
            db.session.rollback()
            flash('Erro ao atualizar indicador.', 'error')
    
    return render_template('indicadores/form.html', 
                         indicador=indicador, 
                         setor=indicador.setor)

@indicadores_bp.route('/valor/<int:indicador_id>', methods=['POST'])
@login_required
def adicionar_valor(indicador_id):
    """Adicionar valor ao indicador"""
    indicador = Indicador.query.get_or_404(indicador_id)
    
    try:
        valor_str = request.form.get('valor', '0')
        data_str = request.form.get('data')
        observacao = request.form.get('observacao', '').strip()
        
        # Converter valor
        valor = float(valor_str.replace(',', '.'))
        
        # Converter data mantendo compatibilidade
        if data_str and data_str.strip():
            # Criar datetime com hora zerada para manter consistência
            data_obj = datetime.strptime(data_str, '%Y-%m-%d')
        else:
            data_obj = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Criar valor
        valor_indicador = ValorIndicador(
            valor=valor,
            data=data_obj,
            observacao=observacao,
            indicador_id=indicador_id
        )
        
        db.session.add(valor_indicador)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Valor {valor} registrado para {data_obj.strftime("%d/%m/%Y")}',
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao salvar: {str(e)}")
        return jsonify({
            'success': False, 
            'error': f'Erro: {str(e)}'
        }), 500



@indicadores_bp.route('/historico/<int:indicador_id>')
@login_required
def historico(indicador_id):
    """Visualizar histórico do indicador com tratamento robusto de erros"""
    indicador = Indicador.query.get_or_404(indicador_id)
    
    valores = []
    stats = {}
    
    try:
        # Buscar valores com query raw para evitar problemas de conversão
        from sqlalchemy import text
        
        query = text("""
            SELECT id, valor, data, observacao, data_criacao 
            FROM valor_indicador 
            WHERE indicador_id = :indicador_id 
            ORDER BY data DESC
        """)
        
        result = db.session.execute(query, {'indicador_id': indicador_id})
        
        for row in result:
            try:
                # Tentar converter cada registro individualmente
                data_valor = row.data
                if isinstance(data_valor, str):
                    # Se for string, tentar converter
                    if ' ' in data_valor:
                        data_obj = datetime.strptime(data_valor.split(' ')[0], '%Y-%m-%d')
                    else:
                        data_obj = datetime.strptime(data_valor, '%Y-%m-%d')
                else:
                    # Se já for datetime ou date
                    data_obj = data_valor
                
                # Criar objeto simulado para o template
                valor_obj = type('ValorIndicador', (), {
                    'id': row.id,
                    'valor': row.valor,
                    'data': data_obj,
                    'observacao': row.observacao or '',
                    'data_criacao': row.data_criacao
                })()
                
                valores.append(valor_obj)
                
            except Exception as e:
                print(f"Erro ao processar registro {row.id}: {e}")
                continue
        
        # Calcular estatísticas se houver valores válidos
        if valores:
            valores_numericos = [v.valor for v in valores]
            stats = {
                'total_registros': len(valores),
                'valor_atual': valores[0].valor if valores else None,
                'valor_maximo': max(valores_numericos),
                'valor_minimo': min(valores_numericos),
                'valor_medio': sum(valores_numericos) / len(valores_numericos),
                'variacao': None
            }
        
        print(f"Histórico carregado com sucesso: {len(valores)} registros")
        
    except Exception as e:
        print(f"Erro ao carregar histórico: {e}")
        flash('Erro ao carregar histórico. Alguns dados podem estar corrompidos.', 'warning')
        valores = []
        stats = {}
    
    return render_template('indicadores/historico.html', 
                         indicador=indicador, 
                         valores=valores,
                         stats=stats,
                         dias=30)

@indicadores_bp.route('/excluir/<int:indicador_id>', methods=['POST'])
@login_required
def excluir(indicador_id):
    """Excluir indicador (desativar)"""
    indicador = Indicador.query.get_or_404(indicador_id)
    
    # Verificar permissão (apenas admin ou editor)
    if not current_user.admin:
        acesso = UsuarioSetor.query.filter_by(
            usuario_id=current_user.id,
            setor_id=indicador.setor_id,
            ativo=True
        ).first()
        if not acesso or acesso.permissao == 'visualizar':
            return jsonify({'error': 'Sem permissão'}), 403
    
    try:
        # Desativar ao invés de excluir
        indicador.ativo = False
        db.session.commit()
        
        flash(f'Indicador "{indicador.nome}" removido com sucesso.', 'success')
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Erro ao remover indicador'}), 500

@indicadores_bp.route('/valor/<int:valor_id>/excluir', methods=['DELETE'])
@login_required
def excluir_valor(valor_id):
    """Excluir valor do indicador"""
    valor = ValorIndicador.query.get_or_404(valor_id)
    
    # Verificar permissão
    if not current_user.admin:
        acesso = UsuarioSetor.query.filter_by(
            usuario_id=current_user.id,
            setor_id=valor.indicador.setor_id,
            ativo=True
        ).first()
        if not acesso or acesso.permissao == 'visualizar':
            return jsonify({'success': False, 'error': 'Sem permissão para excluir'}), 403
    
    try:
        indicador_id = valor.indicador_id
        data_valor = valor.data.strftime('%d/%m/%Y') if hasattr(valor.data, 'strftime') else str(valor.data)
        
        db.session.delete(valor)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Valor de {data_valor} excluído com sucesso!'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False, 
            'error': f'Erro ao excluir valor: {str(e)}'
        }), 500

@indicadores_bp.route('/valor/<int:valor_id>/editar', methods=['GET', 'POST'])
@login_required
def editar_valor(valor_id):
    """Editar valor do indicador"""
    valor = ValorIndicador.query.get_or_404(valor_id)
    
    # Verificar permissão
    if not current_user.admin:
        acesso = UsuarioSetor.query.filter_by(
            usuario_id=current_user.id,
            setor_id=valor.indicador.setor_id,
            ativo=True
        ).first()
        if not acesso or acesso.permissao == 'visualizar':
            return jsonify({'success': False, 'error': 'Sem permissão para editar'}), 403
    
    if request.method == 'POST':
        try:
            novo_valor = float(request.form.get('valor', '0').replace(',', '.'))
            nova_data_str = request.form.get('data')
            nova_observacao = request.form.get('observacao', '').strip()
            
            # Converter data
            if nova_data_str:
                nova_data = datetime.strptime(nova_data_str, '%Y-%m-%d')
            else:
                nova_data = valor.data
            
            # Atualizar valor
            valor.valor = novo_valor
            valor.data = nova_data
            valor.observacao = nova_observacao
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': f'Valor atualizado para {nova_data.strftime("%d/%m/%Y")}!',
                'valor_formatado': formatar_valor(novo_valor, valor.indicador.tipo, valor.indicador.unidade)
            })
            
        except Exception as e:
            db.session.rollback()
            return jsonify({
                'success': False, 
                'error': f'Erro ao atualizar valor: {str(e)}'
            }), 500
    
    # GET - Retornar dados para edição
    data_formatada = valor.data.strftime('%Y-%m-%d') if hasattr(valor.data, 'strftime') else str(valor.data).split(' ')[0]
    
    return jsonify({
        'id': valor.id,
        'valor': valor.valor,
        'data': data_formatada,
        'observacao': valor.observacao or ''
    })

@indicadores_bp.route('/<int:indicador_id>/dados-graficos')
@login_required
def dados_graficos(indicador_id):
    """Fornecer dados formatados para os gráficos"""
    indicador = Indicador.query.get_or_404(indicador_id)
    
    # Parâmetros de filtro
    tipo_visualizacao = request.args.get('tipo_visualizacao', 'detalhado')
    tipo_comparacao = request.args.get('tipo_comparacao', 'meta')
    ano_comparacao = request.args.get('ano_comparacao', 'atual')
    periodo_filtro = request.args.get('periodo_filtro', '12')
    
    # Buscar valores do indicador
    valores = ValorIndicador.query.filter_by(indicador_id=indicador_id).order_by(ValorIndicador.data).all()
    
    # Processar dados baseado na periodicidade
    dados_processados = processar_dados_por_periodicidade(valores, indicador.periodicidade, tipo_visualizacao)
    
    # Gerar datasets para cada tipo de gráfico
    datasets = {
        'linha': gerar_dataset_linha(dados_processados, indicador, tipo_comparacao),
        'coluna': gerar_dataset_coluna(dados_processados, indicador, tipo_comparacao),
        'barra': gerar_dataset_barra(dados_processados, indicador, tipo_comparacao),
        'rosca': gerar_dataset_rosca(dados_processados, indicador)
    }
    
    # Calcular performance
    performance = calcular_performance(dados_processados, indicador)
    
    return jsonify({
        'labels': dados_processados['labels'],
        'datasets': datasets,
        'performance_ultimo_periodo': performance['ultimo_periodo'],
        'performance_acumulada': performance['acumulada'],
        'resumo_rosca': gerar_resumo_rosca(dados_processados)
    })

def processar_dados_por_periodicidade(valores, periodicidade, tipo_visualizacao):
    """Processar dados baseado na periodicidade do indicador"""
    # Implementar lógica de agrupamento por periodicidade
    # Retornar dados organizados por período
    pass

def gerar_dataset_linha(dados, indicador, tipo_comparacao):
    """Gerar dataset específico para gráfico de linha"""
    # Implementar geração de dataset para linha
    pass

def calcular_performance(dados, indicador):
    """Calcular performance em relação às metas"""
    # Implementar cálculo de performance
    pass
