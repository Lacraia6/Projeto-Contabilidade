from flask import Blueprint, session, jsonify, request
from app.models import Usuario

bp = Blueprint('api_global', __name__, url_prefix='/api')


@bp.get('/usuarios')
def api_usuarios():
    """API global para buscar usuários"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'message': 'Usuário não autenticado'}), 401
        
        # Verificar se é admin, gerente ou supervisor
        usuario = Usuario.query.get(user_id)
        if not usuario or usuario.tipo not in ['admin', 'gerente', 'supervisor']:
            return jsonify({'success': False, 'message': 'Acesso negado'}), 403
        
        # Verificar se há parâmetro de busca
        query_param = request.args.get('q', '').strip()
        
        # Buscar usuários baseado no tipo do usuário logado
        if usuario.tipo == 'admin':
            # Admin vê todos os usuários
            if query_param:
                usuarios = Usuario.query.filter(
                    Usuario.nome.ilike(f'%{query_param}%'),
                    Usuario.ativo == True
                ).order_by(Usuario.nome).limit(10).all()
            else:
                usuarios = Usuario.query.filter_by(ativo=True).order_by(Usuario.nome).all()
        elif usuario.tipo == 'gerente':
            # Gerente vê usuários do seu setor
            if query_param:
                usuarios = Usuario.query.filter(
                    Usuario.nome.ilike(f'%{query_param}%'),
                    Usuario.ativo == True,
                    Usuario.setor_id == usuario.setor_id
                ).order_by(Usuario.nome).limit(10).all()
            else:
                usuarios = Usuario.query.filter_by(ativo=True, setor_id=usuario.setor_id).order_by(Usuario.nome).all()
        else:  # supervisor
            # Supervisor vê usuários normais
            if query_param:
                usuarios = Usuario.query.filter(
                    Usuario.nome.ilike(f'%{query_param}%'),
                    Usuario.ativo == True,
                    Usuario.tipo == 'normal'
                ).order_by(Usuario.nome).limit(10).all()
            else:
                usuarios = Usuario.query.filter_by(ativo=True, tipo='normal').order_by(Usuario.nome).all()
        
        usuarios_data = []
        for u in usuarios:
            usuarios_data.append({
                'id': u.id,
                'nome': u.nome,
                'login': u.login,
                'tipo': u.tipo,
                'setor_id': u.setor_id,
                'ativo': u.ativo
            })
        
        return jsonify({
            'success': True,
            'usuarios': usuarios_data
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'}), 500


