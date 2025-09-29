from flask import Blueprint, render_template, request, session, jsonify, redirect, url_for
from app.db import db
from app.models import Usuario, Checklist, ChecklistItem, ChecklistItemConclusao, Empresa
from datetime import datetime

bp = Blueprint('checklist', __name__, url_prefix='/checklist')


@bp.get('')
@bp.get('/')
def index():
    """Página principal do painel de checklists do usuário"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return redirect(url_for('auth.login'))
        
        # Buscar usuário
        usuario = Usuario.query.get(user_id)
        if not usuario:
            return redirect(url_for('auth.login'))
        
        # Buscar checklists do usuário
        checklists = db.session.query(Checklist, Empresa).join(
            Empresa, Checklist.empresa_id == Empresa.id
        ).filter(
            Checklist.ativo == True,
            Empresa.ativo == True
        ).order_by(Checklist.criado_em.desc()).all()
        
        # Para cada checklist, buscar itens do usuário
        checklists_data = []
        for checklist, empresa in checklists:
            # Buscar itens onde o usuário é responsável
            itens = ChecklistItem.query.filter_by(
                checklist_id=checklist.id,
                responsavel_id=user_id,
                ativo=True
            ).order_by(ChecklistItem.ordem).all()
            
            if itens:  # Só incluir se o usuário tem itens
                # Calcular progresso
                total_itens = len(itens)
                itens_concluidos = 0
                
                for item in itens:
                    conclusao = ChecklistItemConclusao.query.filter_by(
                        item_id=item.id,
                        usuario_id=user_id
                    ).first()
                    
                    if conclusao and conclusao.concluido:
                        itens_concluidos += 1
                
                progresso = (itens_concluidos / total_itens * 100) if total_itens > 0 else 0
                
                checklists_data.append({
                    'checklist': checklist,
                    'empresa': empresa,
                    'total_itens': total_itens,
                    'itens_concluidos': itens_concluidos,
                    'progresso': progresso
                })
        
        return render_template('checklist.html', checklists=checklists_data)
        
    except Exception as e:
        return render_template('checklist.html', error=str(e))


@bp.get('/<int:checklist_id>')
def visualizar_checklist(checklist_id):
    """Visualizar checklist específico"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return redirect(url_for('auth.login'))
        
        # Buscar usuário
        usuario = Usuario.query.get(user_id)
        if not usuario:
            return redirect(url_for('auth.login'))
        
        # Buscar checklist
        checklist = Checklist.query.get(checklist_id)
        if not checklist:
            return render_template('checklist_detalhes.html', error='Checklist não encontrado')
        
        # Verificar se o usuário tem itens neste checklist
        itens = ChecklistItem.query.filter_by(
            checklist_id=checklist_id,
            responsavel_id=user_id,
            ativo=True
        ).order_by(ChecklistItem.ordem).all()
        
        if not itens:
            return render_template('checklist_detalhes.html', error='Você não tem itens neste checklist')
        
        # Buscar conclusões do usuário
        itens_data = []
        for item in itens:
            conclusao = ChecklistItemConclusao.query.filter_by(
                item_id=item.id,
                usuario_id=user_id
            ).first()
            
            itens_data.append({
                'item': item,
                'conclusao': conclusao
            })
        
        return render_template('checklist_detalhes.html', 
                             checklist=checklist, 
                             itens=itens_data)
        
    except Exception as e:
        return render_template('checklist_detalhes.html', error=str(e))


@bp.post('/item/<int:item_id>/concluir')
def concluir_item(item_id):
    """Concluir item do checklist"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'message': 'Usuário não autenticado'}), 401
        
        # Buscar usuário
        usuario = Usuario.query.get(user_id)
        if not usuario:
            return jsonify({'success': False, 'message': 'Usuário não encontrado'}), 404
        
        # Buscar item
        item = ChecklistItem.query.get(item_id)
        if not item:
            return jsonify({'success': False, 'message': 'Item não encontrado'}), 404
        
        # Verificar se o usuário é responsável pelo item
        if item.responsavel_id != user_id:
            return jsonify({'success': False, 'message': 'Você não é responsável por este item'}), 403
        
        data = request.get_json()
        concluido = data.get('concluido', False)
        observacoes = data.get('observacoes', '').strip()
        
        # Buscar ou criar conclusão
        conclusao = ChecklistItemConclusao.query.filter_by(
            item_id=item_id,
            usuario_id=user_id
        ).first()
        
        if not conclusao:
            conclusao = ChecklistItemConclusao(
                item_id=item_id,
                usuario_id=user_id,
                concluido=concluido,
                observacoes=observacoes,
                concluido_em=datetime.now() if concluido else None,
                criado_em=datetime.now()
            )
            db.session.add(conclusao)
        else:
            conclusao.concluido = concluido
            conclusao.observacoes = observacoes
            conclusao.concluido_em = datetime.now() if concluido else None
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Item atualizado com sucesso!'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Erro ao atualizar item: {str(e)}'}), 500


@bp.get('/api/meus-checklists')
def api_meus_checklists():
    """API para buscar checklists do usuário"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'message': 'Usuário não autenticado'}), 401
        
        # Buscar usuário
        usuario = Usuario.query.get(user_id)
        if not usuario:
            return jsonify({'success': False, 'message': 'Usuário não encontrado'}), 404
        
        # Buscar checklists do usuário
        checklists = db.session.query(Checklist, Empresa).join(
            Empresa, Checklist.empresa_id == Empresa.id
        ).filter(
            Checklist.ativo == True,
            Empresa.ativo == True
        ).order_by(Checklist.criado_em.desc()).all()
        
        checklists_data = []
        for checklist, empresa in checklists:
            # Buscar itens onde o usuário é responsável
            itens = ChecklistItem.query.filter_by(
                checklist_id=checklist.id,
                responsavel_id=user_id,
                ativo=True
            ).all()
            
            if itens:  # Só incluir se o usuário tem itens
                # Calcular progresso
                total_itens = len(itens)
                itens_concluidos = 0
                
                for item in itens:
                    conclusao = ChecklistItemConclusao.query.filter_by(
                        item_id=item.id,
                        usuario_id=user_id
                    ).first()
                    
                    if conclusao and conclusao.concluido:
                        itens_concluidos += 1
                
                progresso = (itens_concluidos / total_itens * 100) if total_itens > 0 else 0
                
                checklists_data.append({
                    'id': checklist.id,
                    'nome': checklist.nome,
                    'descricao': checklist.descricao,
                    'empresa_nome': empresa.nome,
                    'total_itens': total_itens,
                    'itens_concluidos': itens_concluidos,
                    'progresso': progresso,
                    'criado_em': checklist.criado_em.strftime('%d/%m/%Y') if checklist.criado_em else None
                })
        
        return jsonify({'success': True, 'checklists': checklists_data})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro ao buscar checklists: {str(e)}'}), 500


@bp.get('/api/checklists-pendentes')
def api_checklists_pendentes():
    """API para buscar número de checklists pendentes do usuário"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'message': 'Usuário não autenticado'}), 401
        
        # Buscar usuário
        usuario = Usuario.query.get(user_id)
        if not usuario:
            return jsonify({'success': False, 'message': 'Usuário não encontrado'}), 404
        
        # Buscar checklists do usuário
        checklists = db.session.query(Checklist, Empresa).join(
            Empresa, Checklist.empresa_id == Empresa.id
        ).filter(
            Checklist.ativo == True,
            Empresa.ativo == True
        ).all()
        
        checklists_pendentes = 0
        for checklist, empresa in checklists:
            # Buscar itens onde o usuário é responsável
            itens = ChecklistItem.query.filter_by(
                checklist_id=checklist.id,
                responsavel_id=user_id,
                ativo=True
            ).all()
            
            if itens:  # Só contar se o usuário tem itens
                # Calcular progresso
                total_itens = len(itens)
                itens_concluidos = 0
                
                for item in itens:
                    conclusao = ChecklistItemConclusao.query.filter_by(
                        item_id=item.id,
                        usuario_id=user_id
                    ).first()
                    
                    if conclusao and conclusao.concluido:
                        itens_concluidos += 1
                
                progresso = (itens_concluidos / total_itens * 100) if total_itens > 0 else 0
                
                # Se não está 100% concluído, é pendente
                if progresso < 100:
                    checklists_pendentes += 1
        
        return jsonify({
            'success': True,
            'checklists_pendentes': checklists_pendentes
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro ao buscar checklists pendentes: {str(e)}'}), 500


@bp.get('/api/checklist/<int:checklist_id>/itens')
def api_checklist_itens(checklist_id):
    """API para buscar itens de um checklist específico"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'message': 'Usuário não autenticado'}), 401
        
        # Buscar usuário
        usuario = Usuario.query.get(user_id)
        if not usuario:
            return jsonify({'success': False, 'message': 'Usuário não encontrado'}), 404
        
        # Buscar checklist
        checklist = Checklist.query.get(checklist_id)
        if not checklist:
            return jsonify({'success': False, 'message': 'Checklist não encontrado'}), 404
        
        # Buscar itens onde o usuário é responsável
        itens = ChecklistItem.query.filter_by(
            checklist_id=checklist_id,
            responsavel_id=user_id,
            ativo=True
        ).order_by(ChecklistItem.ordem).all()
        
        itens_data = []
        for item in itens:
            conclusao = ChecklistItemConclusao.query.filter_by(
                item_id=item.id,
                usuario_id=user_id
            ).first()
            
            itens_data.append({
                'id': item.id,
                'titulo': item.titulo,
                'descricao': item.descricao,
                'ordem': item.ordem,
                'obrigatorio': item.obrigatorio,
                'concluido': conclusao.concluido if conclusao else False,
                'observacoes': conclusao.observacoes if conclusao else '',
                'concluido_em': conclusao.concluido_em.strftime('%d/%m/%Y %H:%M') if conclusao and conclusao.concluido_em else None
            })
        
        return jsonify({
            'success': True,
            'checklist': {
                'id': checklist.id,
                'nome': checklist.nome,
                'descricao': checklist.descricao
            },
            'itens': itens_data
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro ao buscar itens: {str(e)}'}), 500
