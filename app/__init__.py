from flask import Flask, redirect, url_for, request, session
from app.db import db
from datetime import datetime, date

# Armazenamento em memória para dados de exemplo
mock_db = {
	"setores": [
		{"id": 1, "nome": "Departamento Fiscal"},
		{"id": 2, "nome": "Departamento Pessoal"},
		{"id": 3, "nome": "Departamento Contábil"},
	],
	"tributacoes": [
		{"id": 1, "nome": "Simples Nacional"},
		{"id": 2, "nome": "Regime Normal"},
	],
	"usuarios": [
		{"id": 1, "nome": "Ana Gerente", "tipo": "gerente", "setor_id": 1, "login": "ana", "senha": "123"},
		{"id": 2, "nome": "Bruno Colaborador", "tipo": "normal", "setor_id": 1, "login": "bruno", "senha": "123"},
		{"id": 3, "nome": "Carla Colaboradora", "tipo": "normal", "setor_id": 2, "login": "carla", "senha": "123"},
	],
	"empresas": [
		{"id": 101, "nome": "Empresa Alfa", "codigo": "ALFA", "tributacao_id": 1},
		{"id": 102, "nome": "Empresa Beta", "codigo": "BETA", "tributacao_id": 2},
	],
	"tarefas": [
		{"id": 1001, "nome": "Apuração ICMS", "tipo": "Mensal", "descricao": "Apuração mensal de ICMS", "tributacao_id": 2, "setor_id": 1},
		{"id": 1002, "nome": "Folha de Pagamento", "tipo": "Mensal", "descricao": "Processar folha", "tributacao_id": 1, "setor_id": 2},
		{"id": 1003, "nome": "SPED Contábil", "tipo": "Anual", "descricao": "Entrega do SPED", "tributacao_id": 2, "setor_id": 3},
	],
	# vínculos tarefa-empresa-responsável
	"relacionamentos": [
		{"id": 5001, "empresa_id": 101, "tarefa_id": 1001, "responsavel_id": 2, "status": "ativa", "dia_vencimento": 20, "prazo_especifico": None},
		{"id": 5002, "empresa_id": 101, "tarefa_id": 1002, "responsavel_id": 2, "status": "ativa", "dia_vencimento": 5, "prazo_especifico": None},
		{"id": 5003, "empresa_id": 102, "tarefa_id": 1003, "responsavel_id": None, "status": "inativa", "dia_vencimento": None, "prazo_especifico": None},
	],
	# instâncias por período (simplificado)
	"periodos": [
		{"periodo_id": 9001, "relacionamento_id": 5001, "periodo_label": "2025-08", "status": "pendente", "vencimento": "2025-08-20"},
		{"periodo_id": 9002, "relacionamento_id": 5002, "periodo_label": "2025-08", "status": "concluida", "vencimento": "2025-08-05"},
	]
}


def create_app() -> Flask:
	app = Flask(__name__, template_folder="../templates", static_folder="../static")
	app.config["SECRET_KEY"] = "dev-secret-key"
	app.config["AUTH_ENABLED"] = True  # reativado

	# Configuração SQLAlchemy (ajuste usuário/senha/host conforme necessário)
	app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:Tuta1305*@localhost/contabilidade?charset=utf8mb4'
	app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
	db.init_app(app)

	# Filtros Jinja para datas brasileiras
	@app.template_filter('br_date')
	def br_date(value):
		from datetime import datetime, date
		if not value:
			return '-'
		if isinstance(value, (datetime, date)):
			return value.strftime('%d/%m/%Y')
		try:
			parsed = datetime.fromisoformat(str(value))
			return parsed.strftime('%d/%m/%Y')
		except Exception:
			return str(value)

	@app.template_filter('br_period')
	def br_period(value):
		if not value:
			return '-'
		text = str(value)
		parts = text.split('-')
		if len(parts) >= 2 and parts[0].isdigit() and parts[1].isdigit():
			return f"{parts[1]}/{parts[0]}"
		return text

	# Registrar blueprints
	from .blueprints.auth import bp as auth_bp
	from .blueprints.dashboard import bp as dashboard_bp
	from .blueprints.accounts import bp as accounts_bp
	from .blueprints.gerenciamento import bp as gerenciamento_bp
	from .blueprints.empresas import bp as empresas_bp
	from .blueprints.relatorios import bp as relatorios_bp
	from .blueprints.admin import bp as admin_bp
	from .blueprints.tarefas_auto import bp as tarefas_auto_bp

	app.register_blueprint(auth_bp)
	app.register_blueprint(dashboard_bp)
	app.register_blueprint(accounts_bp)
	app.register_blueprint(gerenciamento_bp)
	app.register_blueprint(empresas_bp)
	app.register_blueprint(relatorios_bp)
	app.register_blueprint(admin_bp)
	app.register_blueprint(tarefas_auto_bp)

	# Proteção simples de rotas (respeita flag AUTH_ENABLED)
	PUBLIC_PATHS = {"/login"}

	@app.before_request
	def _require_login():
		if not app.config.get("AUTH_ENABLED", True):
			return None
		path = request.path.rstrip('/') or '/'
		if path.startswith('/static'):
			return None
		if path in PUBLIC_PATHS:
			return None
		if not session.get('user_id'):
			return redirect(url_for('auth.login_page'))
		return None

	return app


