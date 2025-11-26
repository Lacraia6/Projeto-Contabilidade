from flask import Blueprint, request, jsonify, session, current_app
from app.services.empresa_service import EmpresaService
from app.services.tarefa_service import TarefaService
from app.models import Usuario, Tarefa, Empresa
from app.db import db
from app.api_response import success_response

bp = Blueprint('api_v1', __name__, url_prefix='/api/v1')


def _get_cache():
	return getattr(current_app, 'cache', None)


def _cache_key(prefix: str, user_id: int, args: dict) -> str:
	parts = [prefix, f"u:{user_id}"]
	for k in sorted(args.keys()):
		parts.append(f"{k}={args.get(k)}")
	return '|'.join(parts)


@bp.get('/empresas')
def list_empresas():
	"""Unificado: lista/busca empresas com filtros e paginação (centralizado via service)."""
	user_id = session.get('user_id')
	if not user_id:
		return jsonify({'success': False, 'message': 'Usuário não autenticado'}), 401

	usuario = Usuario.query.get(user_id)
	if not usuario:
		return jsonify({'success': False, 'message': 'Usuário inválido'}), 403

	search = request.args.get('q', '').strip()
	page = max(int(request.args.get('page', 1) or 1), 1)
	limit = min(int(request.args.get('limit', 20) or 20), 100)
	setor_id = request.args.get('setor_id', type=int)
	ativo = request.args.get('ativo')
	ativo_bool = None if ativo is None else (str(ativo).lower() in ['1', 'true', 't', 'yes', 'sim'])

	# Cache
	cache = _get_cache()
	args_for_key = dict(request.args)
	cache_key = _cache_key('empresas', user_id, args_for_key)
	if cache:
		cached = cache.get(cache_key)
		if cached is not None:
			return jsonify(cached)

	# Escopo por papel usando service
	ids_escopo = None
	if usuario.tipo == 'gerente':
		# Gerente: empresas vinculadas a suas tarefas (filtradas por setor se houver)
		empresas_escopo = EmpresaService.get_empresas_por_usuario(user_id, setor_id or usuario.setor_id)
		ids_escopo = [e.id for e in empresas_escopo]

	# Construir query base
	query = Empresa.query
	if ids_escopo is not None:
		if len(ids_escopo) == 0:
			# Sem acesso a nenhuma empresa
			pagination = {
				'total': 0,
				'page': page,
				'limit': limit,
				'total_pages': 0,
			}
			response = success_response(data=[], pagination=pagination)
			if cache:
				cache.set(cache_key, response)
			return jsonify(response)
		query = query.filter(Empresa.id.in_(ids_escopo))

	# Filtros
	if ativo_bool is not None:
		query = query.filter(Empresa.ativo == ativo_bool)
	if search:
		query = query.filter(Empresa.nome.ilike(f'%{search}%'))

	# Paginação
	total = query.count()
	items = query.order_by(Empresa.nome).offset((page - 1) * limit).limit(limit).all()
	data = [{
		'id': e.id,
		'nome': e.nome,
		'codigo': getattr(e, 'codigo', None)
	} for e in items]

	response = success_response(
		data=data,
		pagination={
			'total': total,
			'page': page,
			'limit': limit,
			'total_pages': (total + limit - 1) // limit,
		}
	)
	if cache:
		cache.set(cache_key, response)
	return jsonify(response)


@bp.get('/tarefas')
def list_tarefas():
	"""Unificado: lista/busca tarefas com filtros e paginação (centralizado via service)."""
	user_id = session.get('user_id')
	if not user_id:
		return jsonify({'success': False, 'message': 'Usuário não autenticado'}), 401

	usuario = Usuario.query.get(user_id)
	if not usuario:
		return jsonify({'success': False, 'message': 'Usuário inválido'}), 403

	search = request.args.get('q', '').strip()
	page = max(int(request.args.get('page', 1) or 1), 1)
	limit = min(int(request.args.get('limit', 20) or 20), 100)
	setor_id = request.args.get('setor_id', type=int)
	tipo = request.args.get('tipo')  # Mensal, Anual, etc.

	# Cache
	cache = _get_cache()
	args_for_key = dict(request.args)
	cache_key = _cache_key('tarefas', user_id, args_for_key)
	if cache:
		cached = cache.get(cache_key)
		if cached is not None:
			return jsonify(cached)

	# Escopo via service para gerente
	ids_escopo = None
	if usuario.tipo == 'gerente':
		tarefas_escopo = TarefaService.get_tarefas_por_usuario(user_id, setor_id or usuario.setor_id)
		ids_escopo = [t.id for t in tarefas_escopo]

	# Construir query base
	query = Tarefa.query
	if ids_escopo is not None:
		if len(ids_escopo) == 0:
			pagination = {
				'total': 0,
				'page': page,
				'limit': limit,
				'total_pages': 0,
			}
			response = success_response(data=[], pagination=pagination)
			if cache:
				cache.set(cache_key, response)
			return jsonify(response)
		query = query.filter(Tarefa.id.in_(ids_escopo))

	# Filtros
	if search:
		query = query.filter(Tarefa.nome.ilike(f'%{search}%'))
	if setor_id:
		query = query.filter(Tarefa.setor_id == setor_id)
	if tipo:
		query = query.filter(Tarefa.tipo == tipo)

	# Paginação
	total = query.count()
	items = query.order_by(Tarefa.nome).offset((page - 1) * limit).limit(limit).all()
	data = [{
		'id': t.id,
		'nome': t.nome,
		'tipo': t.tipo,
		'setor_id': t.setor_id,
		'tributacao_id': getattr(t, 'tributacao_id', None)
	} for t in items]

	response = success_response(
		data=data,
		pagination={
			'total': total,
			'page': page,
			'limit': limit,
			'total_pages': (total + limit - 1) // limit,
		}
	)
	if cache:
		cache.set(cache_key, response)
	return jsonify(response)


# Helpers de invalidação (serão usados por endpoints de mutação futuramente)

def invalidate_empresas_cache():
	cache = _get_cache()
	if not cache:
		return
	try:
		cache.clear()
	except Exception:
		pass


def invalidate_tarefas_cache():
	cache = _get_cache()
	if not cache:
		return
	try:
		cache.clear()
	except Exception:
		pass
