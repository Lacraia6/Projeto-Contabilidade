from flask import Flask, redirect, url_for, request, session, render_template
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
		{"periodo_id": 9001, "relacionamento_id": 5001, "periodo_label": "2025-09", "status": "pendente", "vencimento": "2025-09-20"},
		{"periodo_id": 9002, "relacionamento_id": 5002, "periodo_label": "2025-09", "status": "concluida", "vencimento": "2025-09-05"},
	]
}


def create_app() -> Flask:
	app = Flask(__name__, template_folder="../templates", static_folder="../static")
	app.config["SECRET_KEY"] = "dev-secret-key"
	app.config["AUTH_ENABLED"] = True  # reativado

	# Configuração SQLAlchemy MySQL
	app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:Tuta1305*@localhost/contabilidade?charset=utf8mb4'
	app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
	
	# Configuração de Cache
	app.config['CACHE_TYPE'] = 'simple'  # Use 'redis' em produção
	app.config['CACHE_DEFAULT_TIMEOUT'] = 300  # 5 minutos
	
	# Configuração de Rate Limiting
	app.config['RATELIMIT_ENABLED'] = True
	app.config['RATELIMIT_STORAGE_URL'] = 'memory://'  # Use 'redis://' em produção
	
	db.init_app(app)
	
	# Inicializar extensões
	try:
		from flask_caching import Cache
		cache = Cache()
		cache.init_app(app)
		app.cache = cache
	except ImportError:
		app.logger.warning("Flask-Caching não instalado. Cache desabilitado.")
	
	try:
		from flask_limiter import Limiter
		from flask_limiter.util import get_remote_address
		limiter = Limiter(
			app=app,
			key_func=get_remote_address,
			default_limits=["200 per day", "50 per hour"],
			storage_uri='memory://'  # Use Redis em produção
		)
		app.limiter = limiter
	except ImportError:
		app.logger.warning("Flask-Limiter não instalado. Rate limiting desabilitado.")

	# Configuração de logging
	import logging
	from logging.handlers import RotatingFileHandler
	import os
	
	if not app.debug and not app.testing:
		if not os.path.exists('logs'):
			os.mkdir('logs')
		file_handler = RotatingFileHandler('logs/contabilidade.log', maxBytes=10240, backupCount=10)
		file_handler.setFormatter(logging.Formatter(
			'%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
		))
		file_handler.setLevel(logging.INFO)
		app.logger.addHandler(file_handler)
		app.logger.setLevel(logging.INFO)
		app.logger.info('Contabilidade application startup')

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

	# Funções globais para templates
	@app.template_global()
	def get_previous_period():
		"""Retorna o período anterior (MM/AAAA)"""
		from .utils import get_previous_period
		return get_previous_period()

	@app.template_global()
	def get_previous_period_label():
		"""Retorna o período anterior (YYYY-MM)"""
		from .utils import get_previous_period_label
		return get_previous_period_label()

	@app.template_global()
	def get_current_period():
		"""Retorna o período atual (MM/AAAA)"""
		from .utils import get_current_period
		return get_current_period()

	@app.template_global()
	def get_current_period_label():
		"""Retorna o período atual (YYYY-MM)"""
		from .utils import get_current_period_label
		return get_current_period_label()

	# Registrar blueprints
	from .blueprints.auth import bp as auth_bp
	from .blueprints.dashboard import bp as dashboard_bp
	from .blueprints.accounts import bp as accounts_bp
	from .blueprints.gerenciamento import bp as gerenciamento_bp
	from .blueprints.empresas import bp as empresas_bp
	from .blueprints.relatorios import bp as relatorios_bp
	from .blueprints.admin import bp as admin_bp
	from .blueprints.tarefas_auto import bp as tarefas_auto_bp
	from .blueprints.supervisor import bp as supervisor_bp
	from .blueprints.checklist import bp as checklist_bp
	from .blueprints.tarefas_melhoradas import bp as tarefas_melhoradas_bp
	from .blueprints.api_global import bp as api_global_bp
	from .blueprints.sistema_completo_tarefas import bp as sistema_completo_tarefas_bp
	from .blueprints.search import bp as search_bp
	from .blueprints.search_simple import bp as search_simple_bp

	app.register_blueprint(auth_bp)
	app.register_blueprint(dashboard_bp)
	app.register_blueprint(accounts_bp)
	app.register_blueprint(gerenciamento_bp)
	app.register_blueprint(empresas_bp)
	app.register_blueprint(relatorios_bp)
	app.register_blueprint(admin_bp)
	app.register_blueprint(tarefas_auto_bp)
	app.register_blueprint(tarefas_melhoradas_bp)
	app.register_blueprint(api_global_bp)
	app.register_blueprint(supervisor_bp)
	app.register_blueprint(checklist_bp)
	app.register_blueprint(sistema_completo_tarefas_bp)
	app.register_blueprint(search_bp)
	app.register_blueprint(search_simple_bp)

	# Health check endpoint
	@app.route('/health')
	def health_check():
		try:
			# Test database connection
			from sqlalchemy import text
			db.session.execute(text('SELECT 1'))
			return {'status': 'healthy', 'database': 'connected'}, 200
		except Exception as e:
			app.logger.error(f'Health check failed: {e}')
			return {'status': 'unhealthy', 'error': str(e)}, 500

	# Proteção simples de rotas (respeita flag AUTH_ENABLED)
	PUBLIC_PATHS = {"/login", "/health", "/api/search/empresas", "/api/search/tarefas", "/api/search/colaboradores", "/api/search/setores", "/api/search/busca-simples", "/api/search-simple/empresas", "/api/search-simple/tarefas", "/api/search-simple/colaboradores", "/api/search-simple/setores", "/api/search-simple/demo"}

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

	# Error handlers
	@app.errorhandler(404)
	def not_found_error(error):
		app.logger.error(f'404 Error: {request.url}')
		return render_template('error.html', 
			error_code=404, 
			error_message="Página não encontrada"), 404

	@app.errorhandler(500)
	def internal_error(error):
		app.logger.error(f'500 Error: {error}')
		db.session.rollback()
		return render_template('error.html', 
			error_code=500, 
			error_message="Erro interno do servidor"), 500

	@app.errorhandler(Exception)
	def handle_exception(e):
		app.logger.error(f'Unhandled Exception: {e}')
		db.session.rollback()
		return render_template('error.html', 
			error_code=500, 
			error_message="Erro interno do servidor"), 500
	
	# Error handlers customizados para API
	from .exceptions import APIError
	@app.errorhandler(APIError)
	def handle_api_error(error):
		"""Trata erros customizados da API"""
		app.logger.error(f'API Error: {error.message}')
		from flask import jsonify
		return jsonify(error.to_dict()), error.status_code
	
	@app.errorhandler(ValueError)
	def handle_value_error(error):
		"""Trata erros de validação"""
		from flask import jsonify
		app.logger.error(f'Validation Error: {str(error)}')
		return jsonify({
			'success': False,
			'message': str(error),
			'error_type': 'validation_error'
		}), 400

	return app


