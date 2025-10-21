"""
Blueprint para API de Busca Unificada
Sistema centralizado para busca de empresas, tarefas, colaboradores e setores
"""

from flask import Blueprint, request, jsonify, session, render_template
from app.db import db
from app.models import (
    Empresa, Tarefa, Usuario, Setor, Tributacao, RelacionamentoTarefa
)
from sqlalchemy import or_, and_, func
from datetime import datetime
import re

bp = Blueprint('search', __name__, url_prefix='/api/search')


@bp.route('/demo')
def demo_page():
    """Página de demonstração do sistema de busca unificado"""
    return render_template('unified_search_demo.html')

@bp.route('/simple-demo')
def simple_demo_page():
    """Página de demonstração do sistema de busca simples"""
    return render_template('simple_search_demo.html')

@bp.route('/busca-simples')
def busca_simples_page():
    """Página de busca simples e funcional"""
    return render_template('busca_simples.html')


def require_auth():
    """Verifica se o usuário está autenticado"""
    user_id = session.get('user_id')
    if not user_id:
        return None, jsonify({'success': False, 'message': 'Usuário não autenticado'}), 401
    
    usuario = Usuario.query.get(user_id)
    if not usuario:
        return None, jsonify({'success': False, 'message': 'Usuário não encontrado'}), 401
    
    return usuario, None, None


def build_search_query(model, search_term, filters=None):
    """Constrói query de busca genérica"""
    try:
        # Se não há termo de busca, retornar todos os itens (limitado)
        if not search_term or len(search_term.strip()) < 1:
            query = model.query
        else:
            # Limpar e preparar termo de busca
            search_term = search_term.strip()
            search_pattern = f"%{search_term}%"
            
            # Campos de busca baseados no modelo
            if model == Empresa:
                query = model.query.filter(
                    or_(Empresa.nome.ilike(search_pattern), Empresa.codigo.ilike(search_pattern))
                )
            elif model == Tarefa:
                query = model.query.filter(
                    or_(Tarefa.nome.ilike(search_pattern), Tarefa.descricao.ilike(search_pattern))
                )
            elif model == Usuario:
                query = model.query.filter(
                    or_(Usuario.nome.ilike(search_pattern), Usuario.login.ilike(search_pattern))
                )
            elif model == Setor:
                query = model.query.filter(Setor.nome.ilike(search_pattern))
            else:
                # Fallback genérico
                if hasattr(model, 'nome'):
                    query = model.query.filter(model.nome.ilike(search_pattern))
                else:
                    query = model.query
        
        # Aplicar filtros específicos (desabilitado temporariamente)
        # if filters:
        #     query = apply_filters(query, model, filters)
        
        return query
        
    except Exception as e:
        print(f"Erro na build_search_query: {e}")
        # Retornar query básica em caso de erro
        return model.query


def apply_filters(query, model, filters):
    """Aplica filtros específicos baseados no modelo"""
    model_name = model.__name__.lower()
    
    if model_name == 'empresa':
        if filters.get('ativo') == 'true':
            query = query.filter(Empresa.ativo == True)
        
        if filters.get('tributacao') == 'true':
            # Incluir informações de tributação
            query = query.join(Tributacao, Empresa.tributacao_id == Tributacao.id)
    
    elif model_name == 'tarefa':
        if filters.get('tipo') == 'true':
            # Filtrar por tipo específico se necessário
            pass
        
        if filters.get('setor') == 'true':
            # Incluir informações de setor
            query = query.join(Setor, Tarefa.setor_id == Setor.id)
    
    elif model_name == 'usuario':
        if filters.get('ativo') == 'true':
            query = query.filter(Usuario.ativo == True)
        
        if filters.get('setor') == 'true':
            # Incluir informações de setor
            query = query.join(Setor, Usuario.setor_id == Setor.id)
    
    elif model_name == 'setor':
        if filters.get('ativo') == 'true':
            # Assumindo que setores têm campo ativo
            if hasattr(Setor, 'ativo'):
                query = query.filter(Setor.ativo == True)
    
    return query


def format_search_result(item, model_name):
    """Formata resultado de busca baseado no tipo de modelo"""
    try:
        if not item:
            return {
                'id': 0,
                'nome': 'Item não encontrado',
                'descricao': 'Erro',
                'tipo': 'Erro',
                'status': 'erro'
            }
        
        base_result = {
            'id': getattr(item, 'id', 0),
            'nome': getattr(item, 'nome', 'Sem nome')
        }
        
        if model_name == 'empresa':
            base_result.update({
                'codigo': getattr(item, 'codigo', ''),
                'descricao': f"Código: {getattr(item, 'codigo', 'N/A')}",
                'tipo': 'Empresa',
                'status': 'ativo' if getattr(item, 'ativo', True) else 'inativo'
            })
        
        elif model_name == 'tarefa':
            base_result.update({
                'descricao': getattr(item, 'descricao', ''),
                'tipo': getattr(item, 'tipo', 'N/A')
            })
        
        elif model_name == 'usuario':
            base_result.update({
                'descricao': f"Login: {getattr(item, 'login', 'N/A')}",
                'tipo': getattr(item, 'tipo', 'N/A'),
                'status': 'ativo' if getattr(item, 'ativo', True) else 'inativo'
            })
        
        elif model_name == 'setor':
            base_result.update({
                'descricao': f"Setor do sistema",
                'tipo': 'Setor',
                'status': 'ativo' if getattr(item, 'ativo', True) else 'inativo'
            })
        
        return base_result
        
    except Exception as e:
        print(f"Erro ao formatar resultado {model_name}: {e}")
        # Retornar resultado básico em caso de erro
        return {
            'id': 0,
            'nome': 'Erro ao carregar',
            'descricao': 'Erro',
            'tipo': 'Erro',
            'status': 'erro'
        }


@bp.get('/empresas')
def search_empresas():
    """Busca empresas com filtros"""
    # Remover autenticação obrigatória para demo
    usuario = None
    
    try:
        # Parâmetros da requisição
        search_term = request.args.get('q', '').strip()
        page = int(request.args.get('page', 1))
        limit = min(int(request.args.get('limit', 20)), 50)  # Máximo 50 por página
        filters = {k: v for k, v in request.args.items() if k not in ['q', 'page', 'limit']}
        
        # Construir query
        query = build_search_query(Empresa, search_term, filters)
        
        # Aplicar filtros específicos do usuário (desabilitado para demo)
        # if usuario and usuario.tipo == 'gerente' and usuario.setor_id:
        #     # Gerentes só veem empresas relacionadas ao seu setor
        #     query = query.join(RelacionamentoTarefa, Empresa.id == RelacionamentoTarefa.empresa_id)\
        #                  .join(Tarefa, RelacionamentoTarefa.tarefa_id == Tarefa.id)\
        #                  .filter(Tarefa.setor_id == usuario.setor_id)\
        #                  .distinct()
        
        # Contar total
        total = query.count()
        
        # Aplicar paginação
        offset = (page - 1) * limit
        results = query.offset(offset).limit(limit).all()
        
        # Formatar resultados
        formatted_results = [format_search_result(empresa, 'empresa') for empresa in results]
        
        return jsonify({
            'success': True,
            'results': formatted_results,
            'total': total,
            'page': page,
            'limit': limit,
            'total_pages': (total + limit - 1) // limit,
            'has_next': page * limit < total,
            'has_prev': page > 1
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro ao buscar empresas: {str(e)}'
        }), 500


@bp.get('/tarefas')
def search_tarefas():
    """Busca tarefas com filtros"""
    # Remover autenticação obrigatória para demo
    usuario = None
    
    try:
        # Parâmetros da requisição
        search_term = request.args.get('q', '').strip()
        page = int(request.args.get('page', 1))
        limit = min(int(request.args.get('limit', 20)), 50)
        filters = {k: v for k, v in request.args.items() if k not in ['q', 'page', 'limit']}
        
        # Construir query
        query = build_search_query(Tarefa, search_term, filters)
        
        # Aplicar filtros específicos do usuário
        if usuario.tipo == 'gerente' and usuario.setor_id:
            # Gerentes só veem tarefas do seu setor
            query = query.filter(Tarefa.setor_id == usuario.setor_id)
        
        # Contar total
        total = query.count()
        
        # Aplicar paginação
        offset = (page - 1) * limit
        results = query.offset(offset).limit(limit).all()
        
        # Formatar resultados
        formatted_results = []
        print(f"Total de resultados encontrados: {len(results)}")
        for i, tarefa in enumerate(results):
            print(f"Processando tarefa {i}: {tarefa}")
            if tarefa:  # Verificar se não é None
                try:
                    formatted_results.append(format_search_result(tarefa, 'tarefa'))
                except Exception as e:
                    print(f"Erro ao formatar tarefa {i}: {e}")
            else:
                print(f"Tarefa None encontrada na query")
        
        return jsonify({
            'success': True,
            'results': formatted_results,
            'total': total,
            'page': page,
            'limit': limit,
            'total_pages': (total + limit - 1) // limit,
            'has_next': page * limit < total,
            'has_prev': page > 1
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro ao buscar tarefas: {str(e)}'
        }), 500


@bp.get('/colaboradores')
def search_colaboradores():
    """Busca colaboradores com filtros"""
    # Remover autenticação obrigatória para demo
    usuario = None
    
    try:
        # Parâmetros da requisição
        search_term = request.args.get('q', '').strip()
        page = int(request.args.get('page', 1))
        limit = min(int(request.args.get('limit', 20)), 50)
        filters = {k: v for k, v in request.args.items() if k not in ['q', 'page', 'limit']}
        
        # Construir query
        query = build_search_query(Usuario, search_term, filters)
        
        # Aplicar filtros específicos do usuário
        if usuario.tipo == 'gerente' and usuario.setor_id:
            # Gerentes só veem usuários do seu setor
            query = query.filter(Usuario.setor_id == usuario.setor_id)
        
        # Contar total
        total = query.count()
        
        # Aplicar paginação
        offset = (page - 1) * limit
        results = query.offset(offset).limit(limit).all()
        
        # Formatar resultados
        formatted_results = []
        for colaborador in results:
            if colaborador:  # Verificar se não é None
                formatted_results.append(format_search_result(colaborador, 'usuario'))
            else:
                print(f"Colaborador None encontrado na query")
        
        return jsonify({
            'success': True,
            'results': formatted_results,
            'total': total,
            'page': page,
            'limit': limit,
            'total_pages': (total + limit - 1) // limit,
            'has_next': page * limit < total,
            'has_prev': page > 1
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro ao buscar colaboradores: {str(e)}'
        }), 500


@bp.get('/setores')
def search_setores():
    """Busca setores com filtros"""
    # Remover autenticação obrigatória para demo
    usuario = None
    
    try:
        # Parâmetros da requisição
        search_term = request.args.get('q', '').strip()
        page = int(request.args.get('page', 1))
        limit = min(int(request.args.get('limit', 20)), 50)
        filters = {k: v for k, v in request.args.items() if k not in ['q', 'page', 'limit']}
        
        # Construir query
        query = build_search_query(Setor, search_term, filters)
        
        # Contar total
        total = query.count()
        
        # Aplicar paginação
        offset = (page - 1) * limit
        results = query.offset(offset).limit(limit).all()
        
        # Formatar resultados
        formatted_results = [format_search_result(setor, 'setor') for setor in results]
        
        return jsonify({
            'success': True,
            'results': formatted_results,
            'total': total,
            'page': page,
            'limit': limit,
            'total_pages': (total + limit - 1) // limit,
            'has_next': page * limit < total,
            'has_prev': page > 1
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro ao buscar setores: {str(e)}'
        }), 500


@bp.get('/suggestions')
def get_suggestions():
    """Retorna sugestões baseadas no histórico de buscas"""
    usuario, error_response, status_code = require_auth()
    if error_response:
        return error_response, status_code
    
    try:
        search_type = request.args.get('type', 'empresa')
        limit = min(int(request.args.get('limit', 10)), 20)
        
        # Por enquanto, retorna itens mais comuns
        # Futuramente pode implementar histórico de buscas
        suggestions = []
        
        if search_type == 'empresa':
            empresas = Empresa.query.filter(Empresa.ativo == True)\
                                   .order_by(Empresa.nome)\
                                   .limit(limit).all()
            suggestions = [{'id': e.id, 'nome': e.nome} for e in empresas]
        
        elif search_type == 'tarefa':
            tarefas = Tarefa.query.order_by(Tarefa.nome)\
                                 .limit(limit).all()
            suggestions = [{'id': t.id, 'nome': t.nome} for t in tarefas]
        
        elif search_type == 'colaborador':
            colaboradores = Usuario.query.filter(Usuario.ativo == True)\
                                        .order_by(Usuario.nome)\
                                        .limit(limit).all()
            suggestions = [{'id': c.id, 'nome': c.nome} for c in colaboradores]
        
        elif search_type == 'setor':
            setores = Setor.query.order_by(Setor.nome)\
                                .limit(limit).all()
            suggestions = [{'id': s.id, 'nome': s.nome} for s in setores]
        
        return jsonify({
            'success': True,
            'suggestions': suggestions
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro ao buscar sugestões: {str(e)}'
        }), 500


@bp.get('/stats')
def get_search_stats():
    """Retorna estatísticas de busca para o usuário"""
    usuario, error_response, status_code = require_auth()
    if error_response:
        return error_response, status_code
    
    try:
        stats = {
            'empresas': {
                'total': Empresa.query.filter(Empresa.ativo == True).count(),
                'acessivel': 0
            },
            'tarefas': {
                'total': Tarefa.query.count(),
                'acessivel': 0
            },
            'colaboradores': {
                'total': Usuario.query.filter(Usuario.ativo == True).count(),
                'acessivel': 0
            },
            'setores': {
                'total': Setor.query.count(),
                'acessivel': 0
            }
        }
        
        # Calcular acessibilidade baseada no tipo de usuário
        if usuario.tipo == 'gerente' and usuario.setor_id:
            # Gerentes só veem itens do seu setor
            stats['tarefas']['acessivel'] = Tarefa.query.filter(Tarefa.setor_id == usuario.setor_id).count()
            stats['colaboradores']['acessivel'] = Usuario.query.filter(
                Usuario.setor_id == usuario.setor_id,
                Usuario.ativo == True
            ).count()
            
            # Empresas acessíveis via tarefas do setor
            stats['empresas']['acessivel'] = db.session.query(Empresa)\
                .join(RelacionamentoTarefa, Empresa.id == RelacionamentoTarefa.empresa_id)\
                .join(Tarefa, RelacionamentoTarefa.tarefa_id == Tarefa.id)\
                .filter(Tarefa.setor_id == usuario.setor_id)\
                .distinct().count()
        else:
            # Admin vê tudo
            stats['empresas']['acessivel'] = stats['empresas']['total']
            stats['tarefas']['acessivel'] = stats['tarefas']['total']
            stats['colaboradores']['acessivel'] = stats['colaboradores']['total']
        
        stats['setores']['acessivel'] = stats['setores']['total']  # Todos podem ver setores
        
        return jsonify({
            'success': True,
            'stats': stats,
            'user_type': usuario.tipo
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro ao buscar estatísticas: {str(e)}'
        }), 500
