"""
Blueprint V2 para o novo fluxo de vinculação de tarefas
Fluxo: Funcionário → Tarefa → Empresas
"""
from flask import Blueprint, request, session, jsonify, render_template, redirect, url_for
from sqlalchemy import or_
from datetime import datetime

from app.db import db
from app.models import Empresa, Usuario, Tarefa, RelacionamentoTarefa

bp = Blueprint('tarefas_v2', __name__, url_prefix='/tarefas-v2')


@bp.get('/')
def pagina_atribuir():
    """Página principal do novo fluxo de atribuição de tarefas"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return redirect(url_for('auth.login_page'))
        
        usuario = Usuario.query.get(user_id)
        if not usuario or usuario.tipo not in ['admin', 'gerente']:
            return redirect(url_for('auth.login_page'))
        
        # Buscar setores e tributações para o modal de criar tarefa
        from app.models import Setor, Tributacao
        setores = Setor.query.order_by(Setor.nome).all()
        tributacoes = Tributacao.query.order_by(Tributacao.nome).all()
        
        print(f"[V2] Renderizando pagina de atribuicao para {usuario.nome}")
        return render_template(
            'gerente_tarefas_v2.html', 
            usuario=usuario,
            setores=setores,
            tributacoes=tributacoes
        )
        
    except Exception as e:
        print(f"[V2] Erro ao renderizar pagina: {str(e)}")
        return redirect(url_for('auth.login_page'))


@bp.get('/api/funcionarios')
def api_funcionarios():
    """API V2: Busca funcionários do setor do gerente"""
    try:
        print(f"[V2] API funcionarios chamada")
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'message': 'Usuario nao autenticado'}), 401
        
        usuario = Usuario.query.get(user_id)
        if not usuario or usuario.tipo not in ['admin', 'gerente']:
            return jsonify({'success': False, 'message': 'Acesso negado'}), 403
        
        search = request.args.get('q', '').strip()
        limit = request.args.get('limit', type=int) or 50
        limit = max(5, min(limit, 200))
        
        query = Usuario.query.filter(Usuario.ativo == True)
        query = query.filter(Usuario.tipo.in_(['normal', 'gerente']))
        
        # Filtrar por setor do gerente
        if usuario.tipo == 'gerente' and usuario.setor_id:
            query = query.filter(Usuario.setor_id == usuario.setor_id)
            print(f"[V2] Filtrando por setor {usuario.setor_id}")
        
        if search:
            query = query.filter(Usuario.nome.ilike(f'%{search}%'))
        
        funcionarios = query.order_by(Usuario.nome).limit(limit).all()
        
        data = [{
            'id': f.id,
            'nome': f.nome,
            'tipo': f.tipo,
            'setor': f.setor.nome if f.setor else 'N/A'
        } for f in funcionarios]
        
        print(f"[V2] Retornando {len(data)} funcionarios")
        return jsonify({'success': True, 'funcionarios': data})
        
    except Exception as e:
        import traceback
        print(f"[V2] Erro: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'}), 500


@bp.get('/api/tarefas')
def api_tarefas():
    """API V2: Busca tarefas do setor do gerente (exceto anuais)"""
    try:
        print(f"[V2] API tarefas chamada")
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'message': 'Usuario nao autenticado'}), 401
        
        usuario = Usuario.query.get(user_id)
        if not usuario or usuario.tipo not in ['admin', 'gerente']:
            return jsonify({'success': False, 'message': 'Acesso negado'}), 403
        
        search = request.args.get('q', '').strip()
        tributacao_id = request.args.get('tributacao_id', type=int)
        tipo = request.args.get('tipo', '').strip()
        
        query = Tarefa.query
        
        # Filtrar por setor do gerente
        if usuario.tipo == 'gerente' and usuario.setor_id:
            query = query.filter(Tarefa.setor_id == usuario.setor_id)
            print(f"[V2] Filtrando tarefas por setor {usuario.setor_id}")
        
        # EXCLUIR tarefas anuais
        query = query.filter(Tarefa.tipo != 'Anual')
        
        # Filtros opcionais
        if search:
            query = query.filter(Tarefa.nome.ilike(f'%{search}%'))
        
        if tributacao_id:
            query = query.filter(
                or_(
                    Tarefa.tarefa_comum == True,
                    Tarefa.tributacao_id == tributacao_id
                )
            )
        
        if tipo:
            query = query.filter(Tarefa.tipo == tipo)
        
        tarefas = query.order_by(Tarefa.nome).limit(200).all()
        
        data = []
        for t in tarefas:
            data.append({
                'id': t.id,
                'nome': t.nome,
                'tipo': t.tipo,
                'descricao': t.descricao,
                'tributacao_id': t.tributacao_id,
                'tributacao': t.tributacao.nome if t.tributacao else ('Comum' if t.tarefa_comum else 'N/A'),
                'tarefa_comum': t.tarefa_comum,
                'setor': t.setor.nome if t.setor else 'N/A'
            })
        
        print(f"[V2] Retornando {len(data)} tarefas")
        return jsonify({'success': True, 'tarefas': data})
        
    except Exception as e:
        import traceback
        print(f"[V2] Erro: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'}), 500


@bp.get('/api/empresas-disponiveis')
def api_empresas_disponiveis():
    """API V2: Busca empresas que ainda não têm a tarefa vinculada"""
    try:
        print(f"[V2] API empresas-disponiveis chamada")
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'message': 'Usuario nao autenticado'}), 401
        
        usuario = Usuario.query.get(user_id)
        if not usuario or usuario.tipo not in ['admin', 'gerente']:
            return jsonify({'success': False, 'message': 'Acesso negado'}), 403
        
        tarefa_id = request.args.get('tarefa_id', type=int)
        search = request.args.get('q', '').strip()
        
        if not tarefa_id:
            return jsonify({'success': False, 'message': 'tarefa_id e obrigatorio'}), 400
        
        tarefa = Tarefa.query.get(tarefa_id)
        if not tarefa:
            return jsonify({'success': False, 'message': 'Tarefa nao encontrada'}), 404
        
        print(f"[V2] Tarefa: {tarefa.nome} (ID: {tarefa.id})")
        
        query = Empresa.query.filter(Empresa.ativo == True)
        
        # Filtrar por tributação compatível
        if not tarefa.tarefa_comum:
            if tarefa.tributacao_id:
                query = query.filter(Empresa.tributacao_id == tarefa.tributacao_id)
                print(f"[V2] Filtrando empresas por tributacao {tarefa.tributacao_id}")
            else:
                print(f"[V2] Tarefa sem tributacao e nao comum - retornando vazio")
                return jsonify({'success': True, 'empresas': []})
        
        if search:
            query = query.filter(Empresa.nome.ilike(f'%{search}%'))
        
        empresas = query.order_by(Empresa.nome).limit(200).all()
        
        # Buscar empresas já vinculadas
        empresas_vinculadas = db.session.query(RelacionamentoTarefa.empresa_id).filter(
            RelacionamentoTarefa.tarefa_id == tarefa_id,
            RelacionamentoTarefa.versao_atual == True,
            RelacionamentoTarefa.status == 'ativa'
        ).all()
        
        ids_vinculadas = {e[0] for e in empresas_vinculadas} if empresas_vinculadas else set()
        print(f"[V2] Empresas ja vinculadas: {len(ids_vinculadas)}")
        
        data = []
        for e in empresas:
            ja_vinculada = e.id in ids_vinculadas
            
            data.append({
                'id': e.id,
                'nome': e.nome,
                'codigo': e.codigo,
                'tributacao_id': e.tributacao_id,
                'tributacao': e.tributacao.nome if e.tributacao else 'Nao definida',
                'ja_vinculada': ja_vinculada
            })
        
        print(f"[V2] Retornando {len(data)} empresas")
        return jsonify({'success': True, 'empresas': data, 'total': len(data)})
        
    except Exception as e:
        import traceback
        print(f"[V2] Erro: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'}), 500


@bp.post('/api/vincular')
def api_vincular():
    """API V2: Vincula uma tarefa a múltiplas empresas para um funcionário específico"""
    try:
        print(f"[V2] API vincular chamada")
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'message': 'Usuario nao autenticado'}), 401
        
        usuario = Usuario.query.get(user_id)
        if not usuario or usuario.tipo not in ['admin', 'gerente']:
            return jsonify({'success': False, 'message': 'Acesso negado'}), 403
        
        data = request.get_json() or {}
        funcionario_id = data.get('funcionario_id')
        tarefa_id = data.get('tarefa_id')
        empresas_ids = data.get('empresas_ids', [])
        
        print(f"[V2] Dados recebidos:")
        print(f"   - Funcionario ID: {funcionario_id}")
        print(f"   - Tarefa ID: {tarefa_id}")
        print(f"   - Empresas IDs: {empresas_ids}")
        
        # Validações
        if not funcionario_id:
            return jsonify({'success': False, 'message': 'Funcionario nao informado'}), 400
        if not tarefa_id:
            return jsonify({'success': False, 'message': 'Tarefa nao informada'}), 400
        if not empresas_ids or not isinstance(empresas_ids, list) or len(empresas_ids) == 0:
            return jsonify({'success': False, 'message': 'Selecione pelo menos uma empresa'}), 400
        
        funcionario = Usuario.query.get(funcionario_id)
        if not funcionario or not funcionario.ativo:
            return jsonify({'success': False, 'message': 'Funcionario nao encontrado ou inativo'}), 404
        
        if usuario.tipo == 'gerente' and usuario.setor_id:
            if funcionario.setor_id != usuario.setor_id:
                return jsonify({'success': False, 'message': 'Funcionario nao pertence ao seu setor'}), 403
        
        tarefa = Tarefa.query.get(tarefa_id)
        if not tarefa:
            return jsonify({'success': False, 'message': 'Tarefa nao encontrada'}), 404
        
        if usuario.tipo == 'gerente' and usuario.setor_id:
            if tarefa.setor_id != usuario.setor_id:
                return jsonify({'success': False, 'message': 'Tarefa nao pertence ao seu setor'}), 403
        
        if tarefa.tipo == 'Anual':
            return jsonify({'success': False, 'message': 'Tarefas anuais nao podem ser vinculadas via este processo'}), 400
        
        criados = 0
        atualizados = 0
        duplicados = 0
        erros = []
        
        for empresa_id in empresas_ids:
            try:
                empresa = Empresa.query.get(empresa_id)
                if not empresa or not empresa.ativo:
                    erros.append(f'Empresa ID {empresa_id} nao encontrada ou inativa')
                    continue
                
                if not tarefa.tarefa_comum:
                    if tarefa.tributacao_id and empresa.tributacao_id != tarefa.tributacao_id:
                        erros.append(f'Empresa {empresa.nome} tem tributacao incompativel')
                        continue
                
                vinculacao_existente = RelacionamentoTarefa.query.filter_by(
                    empresa_id=empresa_id,
                    tarefa_id=tarefa_id,
                    versao_atual=True,
                    status='ativa'
                ).first()
                
                if vinculacao_existente:
                    if vinculacao_existente.responsavel_id != funcionario_id:
                        responsavel_nome = vinculacao_existente.responsavel.nome if vinculacao_existente.responsavel else 'Desconhecido'
                        print(f"[V2] Duplicata detectada: Empresa {empresa.nome} ja tem tarefa vinculada")
                        erros.append(f'{empresa.nome}: tarefa ja vinculada a {responsavel_nome}')
                        duplicados += 1
                        continue
                    else:
                        duplicados += 1
                        continue
                
                novo_rel = RelacionamentoTarefa(
                    empresa_id=empresa_id,
                    tarefa_id=tarefa_id,
                    responsavel_id=funcionario_id,
                    status='ativa',
                    versao_atual=True,
                    criado_em=datetime.utcnow(),
                    atualizado_em=datetime.utcnow()
                )
                db.session.add(novo_rel)
                criados += 1
                print(f"[V2] Vinculacao criada: {empresa.nome} -> {tarefa.nome} -> {funcionario.nome}")
                
            except Exception as e:
                erros.append(f'Empresa ID {empresa_id}: {str(e)}')
                continue
        
        try:
            db.session.commit()
            print(f"[V2] Commit realizado com sucesso!")
        except Exception as e:
            db.session.rollback()
            print(f"[V2] Erro no commit: {str(e)}")
            return jsonify({'success': False, 'message': f'Erro ao salvar vinculacoes: {str(e)}'}), 500
        
        mensagens = []
        if criados > 0:
            mensagens.append(f'{criados} vinculacao(oes) criada(s)')
        if atualizados > 0:
            mensagens.append(f'{atualizados} atualizada(s)')
        if duplicados > 0:
            mensagens.append(f'{duplicados} ja vinculada(s)')
        
        mensagem_final = ', '.join(mensagens) if mensagens else 'Nenhuma vinculacao realizada'
        
        if erros:
            mensagem_final += f'\n\nAvisos:\n' + '\n'.join(erros[:10])
        
        return jsonify({
            'success': True,
            'message': mensagem_final,
            'criados': criados,
            'atualizados': atualizados,
            'duplicados': duplicados,
            'erros': erros[:10]
        })
        
    except Exception as e:
        db.session.rollback()
        import traceback
        print(f"[V2] Erro: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'}), 500

