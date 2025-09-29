from app.db import db


class Setor(db.Model):
	__tablename__ = 'setores'
	id = db.Column(db.Integer, primary_key=True)
	nome = db.Column(db.String(255), nullable=False)
	
	# Relacionamentos
	usuarios = db.relationship('Usuario', backref='setor', lazy=True)
	tarefas = db.relationship('Tarefa', backref='setor', lazy=True)


class Usuario(db.Model):
	__tablename__ = 'usuarios'
	id = db.Column(db.Integer, primary_key=True)
	nome = db.Column(db.String(255), nullable=False)
	login = db.Column(db.String(150), unique=True, nullable=False)
	senha = db.Column(db.String(255), nullable=False)
	tipo = db.Column(db.String(50), nullable=False)
	setor_id = db.Column(db.Integer, db.ForeignKey('setores.id'))
	criado_em = db.Column(db.TIMESTAMP)
	atualizado_em = db.Column(db.TIMESTAMP)
	ativo = db.Column(db.Boolean, default=True)


class Tributacao(db.Model):
	__tablename__ = 'tributacoes'
	id = db.Column(db.Integer, primary_key=True)
	nome = db.Column(db.String(100), nullable=False)
	
	# Relacionamentos
	empresas = db.relationship('Empresa', backref='tributacao', lazy=True)
	tarefas = db.relationship('Tarefa', backref='tributacao', lazy=True)


class Empresa(db.Model):
	__tablename__ = 'empresas'
	id = db.Column(db.Integer, primary_key=True)
	codigo = db.Column(db.String(100), unique=True, nullable=False)
	nome = db.Column(db.String(255), nullable=False)
	tributacao_id = db.Column(db.Integer, db.ForeignKey('tributacoes.id'))
	criado_em = db.Column(db.TIMESTAMP)
	atualizado_em = db.Column(db.TIMESTAMP)
	ativo = db.Column(db.Boolean, default=True)


class Tarefa(db.Model):
	__tablename__ = 'tarefas'
	id = db.Column(db.Integer, primary_key=True)
	nome = db.Column(db.String(255), nullable=False)
	tipo = db.Column(db.String(50), nullable=False)
	descricao = db.Column(db.Text)
	tributacao_id = db.Column(db.Integer, db.ForeignKey('tributacoes.id'))
	setor_id = db.Column(db.Integer, db.ForeignKey('setores.id'))
	tarefa_comum = db.Column(db.Boolean, default=False)
	condicoes_especiais = db.Column(db.Text)
	criado_em = db.Column(db.TIMESTAMP)
	atualizado_em = db.Column(db.TIMESTAMP)
	
	# Relacionamentos
	tributacoes = db.relationship('TarefaTributacao', backref='tarefa', lazy=True, cascade='all, delete-orphan')


class RelacionamentoTarefa(db.Model):
	__tablename__ = 'relacionamento_tarefas'
	id = db.Column(db.Integer, primary_key=True)
	tarefa_id = db.Column(db.Integer, db.ForeignKey('tarefas.id'), nullable=False)
	empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=False)
	responsavel_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
	vinculacao_id = db.Column(db.Integer, db.ForeignKey('vinculacao_empresa_tributacao.id'))
	status = db.Column(db.String(50), default='ativa')
	dia_vencimento = db.Column(db.Integer)
	prazo_especifico = db.Column(db.Date)
	data_inicio = db.Column(db.Date)
	data_fim = db.Column(db.Date)
	versao_atual = db.Column(db.Boolean, default=True)
	motivo_desativacao = db.Column(db.Text)
	criado_em = db.Column(db.TIMESTAMP)
	atualizado_em = db.Column(db.TIMESTAMP)
	
	# Relacionamentos
	vinculacao = db.relationship('VinculacaoEmpresaTributacao', backref='relacionamentos', lazy=True)


class Periodo(db.Model):
	__tablename__ = 'periodos'
	id = db.Column(db.Integer, primary_key=True)
	relacionamento_tarefa_id = db.Column(db.Integer, db.ForeignKey('relacionamento_tarefas.id'), nullable=False)
	inicio = db.Column(db.Date, nullable=False)
	fim = db.Column(db.Date, nullable=False)
	periodo_label = db.Column(db.String(50), nullable=False)
	status = db.Column(db.String(50), default='pendente')
	data_conclusao = db.Column(db.Date)
	data_retificacao = db.Column(db.Date)
	contador_retificacoes = db.Column(db.Integer, default=0)
	atualizado_em = db.Column(db.TIMESTAMP)
	
	# Relacionamentos
	relacionamento_tarefa = db.relationship('RelacionamentoTarefa', backref='periodos', lazy=True)
	retificacoes = db.relationship('Retificacao', backref='periodo', lazy=True)


class Retificacao(db.Model):
	__tablename__ = 'retificacoes'
	id = db.Column(db.Integer, primary_key=True)
	periodo_id = db.Column(db.Integer, db.ForeignKey('periodos.id'), nullable=False)
	usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
	motivo = db.Column(db.Text)
	criado_em = db.Column(db.TIMESTAMP)


# Novos modelos para sistema de checklists
class Checklist(db.Model):
	__tablename__ = 'checklists'
	id = db.Column(db.Integer, primary_key=True)
	empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=False)
	nome = db.Column(db.String(255), nullable=False)
	descricao = db.Column(db.Text)
	criado_por = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
	criado_em = db.Column(db.TIMESTAMP, default=db.func.current_timestamp())
	ativo = db.Column(db.Boolean, default=True)
	
	# Relacionamentos
	empresa = db.relationship('Empresa', backref='checklists', lazy=True)
	criador = db.relationship('Usuario', backref='checklists_criados', lazy=True)
	itens = db.relationship('ChecklistItem', backref='checklist', lazy=True, cascade='all, delete-orphan')


class ChecklistItem(db.Model):
	__tablename__ = 'checklist_itens'
	id = db.Column(db.Integer, primary_key=True)
	checklist_id = db.Column(db.Integer, db.ForeignKey('checklists.id'), nullable=False)
	titulo = db.Column(db.String(255), nullable=False)
	descricao = db.Column(db.Text)
	ordem = db.Column(db.Integer, default=0)
	responsavel_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
	obrigatorio = db.Column(db.Boolean, default=True)
	ativo = db.Column(db.Boolean, default=True)
	
	# Relacionamentos
	responsavel = db.relationship('Usuario', backref='checklist_itens_responsavel', lazy=True)
	conclusoes = db.relationship('ChecklistItemConclusao', backref='item', lazy=True, cascade='all, delete-orphan')


class ChecklistItemConclusao(db.Model):
    __tablename__ = 'checklist_item_conclusoes'
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('checklist_itens.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    concluido = db.Column(db.Boolean, default=False)
    observacoes = db.Column(db.Text)
    concluido_em = db.Column(db.TIMESTAMP)
    criado_em = db.Column(db.TIMESTAMP, default=db.func.current_timestamp())
    
    # Relacionamentos
    usuario = db.relationship('Usuario', backref='checklist_conclusoes', lazy=True)


class ChecklistItemPredefinido(db.Model):
    __tablename__ = 'checklist_items_predefinidos'
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(255), nullable=False)
    descricao = db.Column(db.Text)
    categoria = db.Column(db.String(100))
    ativo = db.Column(db.Boolean, default=True)
    criado_em = db.Column(db.TIMESTAMP, default=db.func.current_timestamp())
    atualizado_em = db.Column(db.TIMESTAMP, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())


# Novos modelos para sistema de templates de checklists
class ChecklistTemplate(db.Model):
    __tablename__ = 'checklist_templates'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(255), nullable=False)
    descricao = db.Column(db.Text)
    categoria = db.Column(db.String(100))
    ativo = db.Column(db.Boolean, default=True)
    criado_por = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    criado_em = db.Column(db.TIMESTAMP, default=db.func.current_timestamp())
    atualizado_em = db.Column(db.TIMESTAMP, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    
    # Relacionamentos
    criador = db.relationship('Usuario', backref='templates_criados', lazy=True)
    itens = db.relationship('ChecklistTemplateItem', backref='template', lazy=True, cascade='all, delete-orphan')


class ChecklistTemplateItem(db.Model):
    __tablename__ = 'checklist_template_itens'
    id = db.Column(db.Integer, primary_key=True)
    template_id = db.Column(db.Integer, db.ForeignKey('checklist_templates.id'), nullable=False)
    titulo = db.Column(db.String(255), nullable=False)
    descricao = db.Column(db.Text)
    ordem = db.Column(db.Integer, default=0)
    obrigatorio = db.Column(db.Boolean, default=True)
    ativo = db.Column(db.Boolean, default=True)
    criado_em = db.Column(db.TIMESTAMP, default=db.func.current_timestamp())


# ===== NOVOS MODELOS PARA SISTEMA MELHORADO DE TAREFAS =====

class VinculacaoEmpresaTributacao(db.Model):
    __tablename__ = 'vinculacao_empresa_tributacao'
    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=False)
    tributacao_id = db.Column(db.Integer, db.ForeignKey('tributacoes.id'), nullable=False)
    data_inicio = db.Column(db.Date, nullable=False)
    data_fim = db.Column(db.Date)
    ativo = db.Column(db.Boolean, default=True)
    criado_em = db.Column(db.TIMESTAMP, default=db.func.current_timestamp())
    atualizado_em = db.Column(db.TIMESTAMP, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    
    # Relacionamentos
    empresa = db.relationship('Empresa', backref='vinculacoes_tributacao', lazy=True)
    tributacao = db.relationship('Tributacao', backref='vinculacoes_empresas', lazy=True)


class TarefaTributacao(db.Model):
    __tablename__ = 'tarefa_tributacao'
    id = db.Column(db.Integer, primary_key=True)
    tarefa_id = db.Column(db.Integer, db.ForeignKey('tarefas.id'), nullable=False)
    tributacao_id = db.Column(db.Integer, db.ForeignKey('tributacoes.id'), nullable=False)
    obrigatoria = db.Column(db.Boolean, default=True)
    ordem = db.Column(db.Integer, default=0)
    ativo = db.Column(db.Boolean, default=True)
    criado_em = db.Column(db.TIMESTAMP, default=db.func.current_timestamp())
    
    # Relacionamentos
    tributacao = db.relationship('Tributacao', backref='tarefas_vinculadas', lazy=True)


class ConfiguracaoResponsavelPadrao(db.Model):
    __tablename__ = 'configuracao_responsavel_padrao'
    id = db.Column(db.Integer, primary_key=True)
    setor_id = db.Column(db.Integer, db.ForeignKey('setores.id'), nullable=False)
    tributacao_id = db.Column(db.Integer, db.ForeignKey('tributacoes.id'), nullable=False)
    responsavel_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    ativo = db.Column(db.Boolean, default=True)
    criado_em = db.Column(db.TIMESTAMP, default=db.func.current_timestamp())
    atualizado_em = db.Column(db.TIMESTAMP, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    
    # Relacionamentos
    setor = db.relationship('Setor', backref='responsaveis_padrao', lazy=True)
    tributacao = db.relationship('Tributacao', backref='responsaveis_padrao', lazy=True)
    responsavel = db.relationship('Usuario', backref='configuracoes_responsavel', lazy=True)