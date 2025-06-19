from app import db  # IMPORTAÇÃO CRUCIAL QUE ESTÁ FALTANDO
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import json


# Importar db do módulo principal
from app import db, login_manager

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

class Usuario(UserMixin, db.Model):
    """Modelo para usuários do sistema"""
    __tablename__ = 'usuarios'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha_hash = db.Column(db.String(255), nullable=False)
    ativo = db.Column(db.Boolean, default=True)
    admin = db.Column(db.Boolean, default=False)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    setores = db.relationship('UsuarioSetor', backref='usuario', lazy='dynamic')
    
    def set_password(self, senha):
        """Define a senha do usuário"""
        self.senha_hash = generate_password_hash(senha)
    
    def check_password(self, senha):
        """Verifica a senha do usuário"""
        return check_password_hash(self.senha_hash, senha)
    
    def get_setores(self):
        """Retorna os setores que o usuário tem acesso"""
        return [us.setor for us in self.setores if us.ativo]
    
    def __repr__(self):
        return f'<Usuario {self.nome}>'

class Setor(db.Model):
    __tablename__ = 'setores'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False, unique=True)
    descricao = db.Column(db.Text)
    cor = db.Column(db.String(7), default='#007bff')
    ativo = db.Column(db.Boolean, default=True)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    
    # ALTERAR ESTA LINHA
    dashboards = db.relationship('Dashboard', backref='setor', lazy='dynamic')
    usuarios = db.relationship('UsuarioSetor', backref='setor', lazy='dynamic')
    
    def get_indicadores_ativos(self):
        """Retorna indicadores ativos do setor"""
        return self.indicadores.filter_by(ativo=True).all()
    
    def get_dashboard_principal(self):
        """Retorna o dashboard principal do setor"""
        return self.dashboards.filter_by(principal=True, ativo=True).first()
    
    def __repr__(self):
        return f'<Setor {self.nome}>'
    indicadores = db.relationship('Indicador', backref='setor', lazy='dynamic', cascade='all, delete-orphan')

class Indicador(db.Model):
    """Modelo para indicadores/KPIs"""
    __tablename__ = 'indicadores'
    __table_args__ = {'extend_existing': True}  # ADICIONAR ESTA LINHA
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text)
    tipo = db.Column(db.String(50), nullable=False)  # numero, percentual, moeda, tempo
    unidade = db.Column(db.String(20))  # %, R$, min, etc.
    meta = db.Column(db.Float)
    meta_tipo = db.Column(db.String(20), default='maior')  # maior, menor, igual
    cor = db.Column(db.String(7), default='#28a745')
    icone = db.Column(db.String(50), default='fas fa-chart-line')
    ativo = db.Column(db.Boolean, default=True)
    ordem = db.Column(db.Integer, default=0)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign Keys
    setor_id = db.Column(db.Integer, db.ForeignKey('setores.id'), nullable=False)
    
    # Relacionamentos
    valores = db.relationship('ValorIndicador', back_populates='indicador', lazy='dynamic', cascade='all, delete-orphan')
    
    def get_valor_atual(self):
        """Retorna o valor mais recente do indicador"""
        return self.valores.order_by(ValorIndicador.data.desc()).first()
    
    def get_valores_periodo(self, dias=30):
        """Retorna valores dos últimos N dias"""
        from datetime import datetime, timedelta
        data_limite = datetime.utcnow() - timedelta(days=dias)
        return self.valores.filter(ValorIndicador.data >= data_limite).order_by(ValorIndicador.data).all()
    
    def calcular_status(self):
        """Calcula o status baseado na meta"""
        valor_atual = self.get_valor_atual()
        if not valor_atual or not self.meta:
            return 'neutro'
        
        valor = valor_atual.valor
        if self.meta_tipo == 'maior':
            return 'positivo' if valor >= self.meta else 'negativo'
        elif self.meta_tipo == 'menor':
            return 'positivo' if valor <= self.meta else 'negativo'
        else:  # igual
            tolerancia = self.meta * 0.05  # 5% de tolerância
            return 'positivo' if abs(valor - self.meta) <= tolerancia else 'negativo'
    
    def __repr__(self):
        return f'<Indicador {self.nome}>'

class ValorIndicador(db.Model):
    __tablename__ = 'valor_indicador'
    
    id = db.Column(db.Integer, primary_key=True)
    valor = db.Column(db.Float, nullable=False)
    data = db.Column(db.DateTime, nullable=False)  # Usar DateTime em vez de Date
    observacao = db.Column(db.Text)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    indicador_id = db.Column(db.Integer, db.ForeignKey('indicadores.id'), nullable=False)
    indicador = db.relationship('Indicador', back_populates='valores')
    def __repr__(self):
        return f'<ValorIndicador {self.valor} em {self.data}>'

class UsuarioSetor(db.Model):
    """Relacionamento entre usuários e setores"""
    __tablename__ = 'usuario_setor'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    setor_id = db.Column(db.Integer, db.ForeignKey('setores.id'), nullable=False)
    permissao = db.Column(db.String(20), default='visualizar')  # visualizar, editar, admin
    ativo = db.Column(db.Boolean, default=True)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)

class Dashboard(db.Model):
    """Configurações de dashboards por setor"""
    __tablename__ = 'dashboards'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text)
    configuracao = db.Column(db.Text)  # JSON com layout e widgets
    principal = db.Column(db.Boolean, default=False)
    ativo = db.Column(db.Boolean, default=True)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign Keys
    setor_id = db.Column(db.Integer, db.ForeignKey('setores.id'), nullable=False)
    
    def get_configuracao(self):
        """Retorna a configuração como dicionário"""
        if self.configuracao:
            return json.loads(self.configuracao)
        return {}
    
    def set_configuracao(self, config_dict):
        """Define a configuração a partir de um dicionário"""
        self.configuracao = json.dumps(config_dict)
        self.data_atualizacao = datetime.utcnow()
    
    def __repr__(self):
        return f'<Dashboard {self.nome}>'

class GraficoIndicador(db.Model):
    __tablename__ = 'graficos_indicador'
    __table_args__ = {'extend_existing': True}  # Adicionar esta linha
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    tipo = db.Column(db.String(20), nullable=False)
    configuracao = db.Column(db.Text)
    ativo = db.Column(db.Boolean, default=True)
    ordem = db.Column(db.Integer, default=0)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamento
    indicador_id = db.Column(db.Integer, db.ForeignKey('indicadores.id'), nullable=False)
    
    def get_config(self):
        """Obter configuração do gráfico"""
        if self.configuracao:
            import json
            return json.loads(self.configuracao)
        return {}
    
    def set_config(self, config):
        """Definir configuração do gráfico"""
        import json
        self.configuracao = json.dumps(config)

