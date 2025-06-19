from functools import wraps
from flask import abort
from flask_login import current_user

def admin_required(f):
    """Decorator para rotas que exigem privilégios de admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def setor_required(setor_id):
    """Decorator para verificar acesso ao setor"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            
            # Admin tem acesso a tudo
            if current_user.admin:
                return f(*args, **kwargs)
            
            # Verificar se usuário tem acesso ao setor
            from app.models import UsuarioSetor
            acesso = UsuarioSetor.query.filter_by(
                usuario_id=current_user.id,
                setor_id=setor_id,
                ativo=True
            ).first()
            
            if not acesso:
                abort(403)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def formatar_valor(valor, tipo, unidade=None):
    """Formatar valores para exibição"""
    if valor is None:
        return '-'
    
    if tipo == 'moeda':
        return f'R$ {valor:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
    elif tipo == 'percentual':
        return f'{valor:.1f}%'
    elif tipo == 'numero':
        if valor == int(valor):
            return f'{int(valor):,}'.replace(',', '.')
        return f'{valor:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
    elif tipo == 'tempo':
        if unidade == 'min':
            return f'{int(valor)} min'
        elif unidade == 'h':
            return f'{valor:.1f}h'
    
    return str(valor) + (f' {unidade}' if unidade else '')

def calcular_variacao(valor_atual, valor_anterior):
    """Calcular variação percentual entre dois valores"""
    if not valor_anterior or valor_anterior == 0:
        return None
    
    variacao = ((valor_atual - valor_anterior) / valor_anterior) * 100
    return round(variacao, 1)
