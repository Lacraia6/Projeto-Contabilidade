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
	criado_em = db.Column(db.TIMESTAMP)
	atualizado_em = db.Column(db.TIMESTAMP)


class RelacionamentoTarefa(db.Model):
	__tablename__ = 'relacionamento_tarefas'
	id = db.Column(db.Integer, primary_key=True)
	tarefa_id = db.Column(db.Integer, db.ForeignKey('tarefas.id'), nullable=False)
	empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=False)
	responsavel_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
	status = db.Column(db.String(50), default='ativa')
	dia_vencimento = db.Column(db.Integer)
	prazo_especifico = db.Column(db.Date)
	criado_em = db.Column(db.TIMESTAMP)
	atualizado_em = db.Column(db.TIMESTAMP)


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
