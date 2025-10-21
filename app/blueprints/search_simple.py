from flask import Blueprint, request, jsonify, render_template
from app.db import db
from app.models import Empresa, Tarefa, Usuario, Setor

bp = Blueprint('search_simple', __name__, url_prefix='/api/search-simple')

@bp.route('/empresas')
def search_empresas():
    """Busca empresas - versão simples"""
    try:
        search_term = request.args.get('q', '').strip()
        
        if search_term:
            empresas = Empresa.query.filter(
                Empresa.nome.ilike(f'%{search_term}%')
            ).limit(20).all()
        else:
            empresas = Empresa.query.limit(20).all()
        
        results = []
        for empresa in empresas:
            results.append({
                'id': empresa.id,
                'nome': empresa.nome,
                'codigo': getattr(empresa, 'codigo', ''),
                'descricao': f"Código: {getattr(empresa, 'codigo', 'N/A')}",
                'tipo': 'Empresa',
                'status': 'ativo' if getattr(empresa, 'ativo', True) else 'inativo'
            })
        
        return jsonify({
            'success': True,
            'results': results,
            'total': len(results)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro: {str(e)}'
        }), 500

@bp.route('/tarefas')
def search_tarefas():
    """Busca tarefas - versão simples"""
    try:
        search_term = request.args.get('q', '').strip()
        
        if search_term:
            tarefas = Tarefa.query.filter(
                Tarefa.nome.ilike(f'%{search_term}%')
            ).limit(20).all()
        else:
            tarefas = Tarefa.query.limit(20).all()
        
        results = []
        for tarefa in tarefas:
            results.append({
                'id': tarefa.id,
                'nome': tarefa.nome,
                'descricao': getattr(tarefa, 'descricao', ''),
                'tipo': getattr(tarefa, 'tipo', 'N/A')
            })
        
        return jsonify({
            'success': True,
            'results': results,
            'total': len(results)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro: {str(e)}'
        }), 500

@bp.route('/colaboradores')
def search_colaboradores():
    """Busca colaboradores - versão simples"""
    try:
        search_term = request.args.get('q', '').strip()
        
        if search_term:
            usuarios = Usuario.query.filter(
                Usuario.nome.ilike(f'%{search_term}%')
            ).limit(20).all()
        else:
            usuarios = Usuario.query.limit(20).all()
        
        results = []
        for usuario in usuarios:
            results.append({
                'id': usuario.id,
                'nome': usuario.nome,
                'descricao': f"Login: {getattr(usuario, 'login', 'N/A')}",
                'tipo': getattr(usuario, 'tipo', 'N/A'),
                'status': 'ativo' if getattr(usuario, 'ativo', True) else 'inativo'
            })
        
        return jsonify({
            'success': True,
            'results': results,
            'total': len(results)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro: {str(e)}'
        }), 500

@bp.route('/setores')
def search_setores():
    """Busca setores - versão simples"""
    try:
        search_term = request.args.get('q', '').strip()
        
        if search_term:
            setores = Setor.query.filter(
                Setor.nome.ilike(f'%{search_term}%')
            ).limit(20).all()
        else:
            setores = Setor.query.limit(20).all()
        
        results = []
        for setor in setores:
            results.append({
                'id': setor.id,
                'nome': setor.nome,
                'descricao': 'Setor do sistema',
                'tipo': 'Setor',
                'status': 'ativo' if getattr(setor, 'ativo', True) else 'inativo'
            })
        
        return jsonify({
            'success': True,
            'results': results,
            'total': len(results)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro: {str(e)}'
        }), 500

@bp.route('/demo')
def demo_page():
    """Página de demonstração"""
    return render_template('busca_simples.html')
