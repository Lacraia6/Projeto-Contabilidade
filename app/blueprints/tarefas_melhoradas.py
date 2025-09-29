from flask import Blueprint, render_template, request, session, jsonify, redirect, url_for
from app.db import db
from app.models import (
    Empresa, Tributacao, Usuario, Tarefa, RelacionamentoTarefa, Setor,
    VinculacaoEmpresaTributacao, TarefaTributacao, ConfiguracaoResponsavelPadrao
)
from datetime import datetime, date
import json

bp = Blueprint('tarefas_melhoradas', __name__, url_prefix='/tarefas-melhoradas')


@bp.get('/')
def dashboard():
    """Dashboard principal do sistema melhorado de tarefas"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return redirect(url_for('auth.login'))
        
        # Verificar se é admin ou gerente
        usuario = Usuario.query.get(user_id)
        if not usuario or usuario.tipo not in ['admin', 'gerente']:
            return redirect(url_for('auth.login'))
        
        # Buscar dados para o dashboard
        empresas = Empresa.query.filter_by(ativo=True).order_by(Empresa.nome).all()
        tributacoes = Tributacao.query.all()
        setores = Setor.query.all()
        
        # Filtrar tarefas por setor se for gerente
        tarefas_filtradas = []
        if usuario.tipo == 'gerente':
            # Gerente vê apenas tarefas do seu setor
            tarefas_filtradas = Tarefa.query.filter_by(setor_id=usuario.setor_id).all()
        else:
            # Admin vê todas as tarefas
            tarefas_filtradas = Tarefa.query.all()
        
        # Estatísticas
        total_empresas = len(empresas)
        total_tarefas = Tarefa.query.count()
        total_vinculacoes = VinculacaoEmpresaTributacao.query.filter_by(ativo=True).count()
        
        return render_template('tarefas_melhoradas_dashboard.html',
                             empresas=empresas,
                             tributacoes=tributacoes,
                             setores=setores,
                             tarefas_filtradas=tarefas_filtradas,
                             usuario_logado=usuario,
                             total_empresas=total_empresas,
                             total_tarefas=total_tarefas,
                             total_vinculacoes=total_vinculacoes)
        
    except Exception as e:
        return render_template('tarefas_melhoradas_dashboard.html', error=str(e))


@bp.get('/api/empresa/<int:empresa_id>')
def api_empresa_detalhes(empresa_id):
    """API para obter detalhes de uma empresa"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'message': 'Usuário não autenticado'}), 401
        
        empresa = Empresa.query.get(empresa_id)
        if not empresa:
            return jsonify({'success': False, 'message': 'Empresa não encontrada'}), 404
        
        # Buscar vinculação atual
        vinculacao_atual = VinculacaoEmpresaTributacao.query.filter_by(
            empresa_id=empresa_id, ativo=True
        ).first()
        
        # Buscar tarefas ativas
        tarefas_ativas = db.session.query(RelacionamentoTarefa, Tarefa).join(
            Tarefa, RelacionamentoTarefa.tarefa_id == Tarefa.id
        ).filter(
            RelacionamentoTarefa.empresa_id == empresa_id,
            RelacionamentoTarefa.versao_atual == True
        ).all()
        
        # Buscar histórico de vinculações
        historico_vinculacoes = VinculacaoEmpresaTributacao.query.filter_by(
            empresa_id=empresa_id
        ).order_by(VinculacaoEmpresaTributacao.data_inicio.desc()).all()
        
        return jsonify({
            'success': True,
            'empresa': {
                'id': empresa.id,
                'nome': empresa.nome,
                'codigo': empresa.codigo,
                'tributacao_atual': {
                    'id': vinculacao_atual.tributacao.id if vinculacao_atual else None,
                    'nome': vinculacao_atual.tributacao.nome if vinculacao_atual else None
                } if vinculacao_atual else None,
                'tarefas_ativas': len(tarefas_ativas),
                'historico_vinculacoes': len(historico_vinculacoes)
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'}), 500


@bp.post('/api/vincular-responsavel')
def api_vincular_responsavel():
    """API para vincular responsável a tarefas"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'message': 'Usuário não autenticado'}), 401
        
        # Verificar tipo de usuário
        usuario = Usuario.query.get(user_id)
        if not usuario or usuario.tipo not in ['admin', 'gerente']:
            return jsonify({'success': False, 'message': 'Acesso negado'}), 403
        
        data = request.get_json()
        
        if not data.get('responsavel_id') or not data.get('tarefas'):
            return jsonify({'success': False, 'message': 'Dados obrigatórios não fornecidos'}), 400
        
        responsavel_id = data['responsavel_id']
        tarefas = data['tarefas']
        
        # Verificar se responsável existe
        responsavel = Usuario.query.get(responsavel_id)
        if not responsavel:
            return jsonify({'success': False, 'message': 'Responsável não encontrado'}), 404
        
        vinculacoes_criadas = 0
        
        for tarefa_id in tarefas:
            # Verificar se tarefa existe
            tarefa = Tarefa.query.get(tarefa_id)
            if not tarefa:
                continue
            
            # Verificar se já existe vinculação
            vinculacao_existente = RelacionamentoTarefa.query.filter_by(
                tarefa_id=tarefa_id,
                responsavel_id=responsavel_id,
                ativo=True
            ).first()
            
            if not vinculacao_existente:
                # Criar nova vinculação
                vinculacao = RelacionamentoTarefa(
                    tarefa_id=tarefa_id,
                    responsavel_id=responsavel_id,
                    ativo=True,
                    dia_vencimento=1,  # Dia padrão
                    prazo_especifico=None
                )
                
                db.session.add(vinculacao)
                vinculacoes_criadas += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': f'{vinculacoes_criadas} vinculação(ões) criada(s) com sucesso!'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'}), 500


@bp.get('/api/empresa/<int:empresa_id>/tarefas')
def api_empresa_tarefas(empresa_id):
    """API para obter tarefas de uma empresa"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'message': 'Usuário não autenticado'}), 401
        
        # Buscar tarefas ativas
        tarefas_ativas = db.session.query(RelacionamentoTarefa, Tarefa, Usuario).join(
            Tarefa, RelacionamentoTarefa.tarefa_id == Tarefa.id
        ).outerjoin(
            Usuario, RelacionamentoTarefa.responsavel_id == Usuario.id
        ).filter(
            RelacionamentoTarefa.empresa_id == empresa_id,
            RelacionamentoTarefa.versao_atual == True
        ).all()
        
        # Buscar tarefas históricas
        tarefas_historicas = db.session.query(RelacionamentoTarefa, Tarefa, Usuario).join(
            Tarefa, RelacionamentoTarefa.tarefa_id == Tarefa.id
        ).outerjoin(
            Usuario, RelacionamentoTarefa.responsavel_id == Usuario.id
        ).filter(
            RelacionamentoTarefa.empresa_id == empresa_id,
            RelacionamentoTarefa.versao_atual == False
        ).all()
        
        tarefas_data = {
            'ativas': [],
            'historicas': []
        }
        
        for rel, tarefa, responsavel in tarefas_ativas:
            tarefas_data['ativas'].append({
                'id': rel.id,
                'tarefa_id': tarefa.id,
                'nome': tarefa.nome,
                'tipo': tarefa.tipo,
                'descricao': tarefa.descricao,
                'responsavel': {
                    'id': responsavel.id if responsavel else None,
                    'nome': responsavel.nome if responsavel else 'Sem responsável'
                },
                'status': rel.status,
                'data_inicio': rel.data_inicio.isoformat() if rel.data_inicio else None
            })
        
        for rel, tarefa, responsavel in tarefas_historicas:
            tarefas_data['historicas'].append({
                'id': rel.id,
                'tarefa_id': tarefa.id,
                'nome': tarefa.nome,
                'tipo': tarefa.tipo,
                'descricao': tarefa.descricao,
                'responsavel': {
                    'id': responsavel.id if responsavel else None,
                    'nome': responsavel.nome if responsavel else 'Sem responsável'
                },
                'status': rel.status,
                'data_inicio': rel.data_inicio.isoformat() if rel.data_inicio else None,
                'data_fim': rel.data_fim.isoformat() if rel.data_fim else None,
                'motivo_desativacao': rel.motivo_desativacao
            })
        
        return jsonify({
            'success': True,
            'tarefas': tarefas_data
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'}), 500


@bp.get('/api/tarefas')
def api_tarefas():
    """API para obter todas as tarefas"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'message': 'Usuário não autenticado'}), 401
        
        # Verificar tipo de usuário
        usuario = Usuario.query.get(user_id)
        if not usuario or usuario.tipo not in ['admin', 'gerente']:
            return jsonify({'success': False, 'message': 'Acesso negado'}), 403
        
        # Buscar tarefas
        query = Tarefa.query
        
        # Filtrar por setor se for gerente
        if usuario.tipo == 'gerente':
            query = query.filter(Tarefa.setor_id == usuario.setor_id)
        
        tarefas = query.all()
        
        tarefas_data = []
        for tarefa in tarefas:
            tarefas_data.append({
                'id': tarefa.id,
                'nome': tarefa.nome,
                'tipo': tarefa.tipo,
                'descricao': tarefa.descricao,
                'tributacao': None,  # Será preenchido via TarefaTributacao se necessário
                'setor': tarefa.setor.nome if hasattr(tarefa, 'setor') and tarefa.setor else None,
                'tarefa_comum': tarefa.tarefa_comum,
                'obrigatoria': True  # Por padrão, todas as tarefas são obrigatórias
            })
        
        return jsonify({'success': True, 'tarefas': tarefas_data})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'}), 500


@bp.post('/api/tarefas')
def api_criar_tarefa():
    """API para criar nova tarefa"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'message': 'Usuário não autenticado'}), 401
        
        # Verificar tipo de usuário
        usuario = Usuario.query.get(user_id)
        if not usuario or usuario.tipo not in ['admin', 'gerente']:
            return jsonify({'success': False, 'message': 'Acesso negado'}), 403
        
        data = request.get_json()
        
        # Validar dados obrigatórios
        if not data.get('nome') or not data.get('tipo') or not data.get('setor_id') or not data.get('tributacao_id'):
            return jsonify({'success': False, 'message': 'Dados obrigatórios não fornecidos'}), 400
        
        # Criar nova tarefa
        tarefa = Tarefa(
            nome=data['nome'],
            tipo=data['tipo'],
            descricao=data.get('descricao', ''),
            setor_id=data['setor_id'],
            tributacao_id=data['tributacao_id'],
            tarefa_comum=data.get('tarefa_comum', False)
        )
        
        db.session.add(tarefa)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Tarefa criada com sucesso!', 'tarefa_id': tarefa.id})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'}), 500


@bp.delete('/api/tarefas/<int:tarefa_id>')
def api_excluir_tarefa(tarefa_id):
    """API para excluir tarefa"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'message': 'Usuário não autenticado'}), 401
        
        # Verificar tipo de usuário
        usuario = Usuario.query.get(user_id)
        if not usuario or usuario.tipo not in ['admin', 'gerente']:
            return jsonify({'success': False, 'message': 'Acesso negado'}), 403
        
        tarefa = Tarefa.query.get(tarefa_id)
        if not tarefa:
            return jsonify({'success': False, 'message': 'Tarefa não encontrada'}), 404
        
        db.session.delete(tarefa)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Tarefa excluída com sucesso!'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'}), 500


@bp.get('/api/tarefas/buscar')
def api_buscar_tarefas():
    """API para buscar tarefas por nome"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'message': 'Usuário não autenticado'}), 401
        
        # Verificar tipo de usuário
        usuario = Usuario.query.get(user_id)
        if not usuario or usuario.tipo not in ['admin', 'gerente']:
            return jsonify({'success': False, 'message': 'Acesso negado'}), 403
        
        query_param = request.args.get('q', '').strip()
        if len(query_param) < 2:
            return jsonify({'success': True, 'tarefas': []})
        
        # Buscar tarefas
        search_query = Tarefa.query.filter(Tarefa.nome.ilike(f'%{query_param}%'))
        
        # Filtrar por setor se for gerente
        if usuario.tipo == 'gerente':
            search_query = search_query.filter(Tarefa.setor_id == usuario.setor_id)
        
        tarefas = search_query.limit(10).all()
        
        tarefas_data = []
        for tarefa in tarefas:
            tarefas_data.append({
                'id': tarefa.id,
                'nome': tarefa.nome,
                'tipo': tarefa.tipo
            })
        
        return jsonify({'success': True, 'tarefas': tarefas_data})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'}), 500


@bp.get('/api/tributacao/<int:tributacao_id>/tarefas')
def api_tributacao_tarefas(tributacao_id):
    """API para obter tarefas de uma tributação"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'message': 'Usuário não autenticado'}), 401
        
        # Verificar tipo de usuário
        usuario = Usuario.query.get(user_id)
        if not usuario or usuario.tipo not in ['admin', 'gerente']:
            return jsonify({'success': False, 'message': 'Acesso negado'}), 403
        
        # Buscar tarefas da tributação
        query = db.session.query(TarefaTributacao, Tarefa).join(
            Tarefa, TarefaTributacao.tarefa_id == Tarefa.id
        ).filter(
            TarefaTributacao.tributacao_id == tributacao_id,
            TarefaTributacao.ativo == True
        )
        
        # Filtrar por setor se for gerente
        if usuario.tipo == 'gerente':
            query = query.filter(Tarefa.setor_id == usuario.setor_id)
        
        tarefas_tributacao = query.order_by(TarefaTributacao.ordem, Tarefa.nome).all()
        
        tarefas_data = []
        for tt, tarefa in tarefas_tributacao:
            tarefas_data.append({
                'id': tarefa.id,
                'nome': tarefa.nome,
                'tipo': tarefa.tipo,
                'descricao': tarefa.descricao,
                'tarefa_comum': tarefa.tarefa_comum,
                'obrigatoria': tt.obrigatoria,
                'ordem': tt.ordem
            })
        
        return jsonify({
            'success': True,
            'tarefas': tarefas_data
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'}), 500


@bp.post('/api/empresa/<int:empresa_id>/alterar-tributacao')
def api_alterar_tributacao(empresa_id):
    """API para alterar tributação de uma empresa"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'message': 'Usuário não autenticado'}), 401
        
        data = request.get_json()
        nova_tributacao_id = data.get('tributacao_id')
        responsaveis = data.get('responsaveis', {})
        motivo = data.get('motivo', 'Mudança de tributação')
        
        if not nova_tributacao_id:
            return jsonify({'success': False, 'message': 'Tributação não informada'}), 400
        
        # Verificar se a empresa existe
        empresa = Empresa.query.get(empresa_id)
        if not empresa:
            return jsonify({'success': False, 'message': 'Empresa não encontrada'}), 404
        
        # Verificar se a nova tributação existe
        nova_tributacao = Tributacao.query.get(nova_tributacao_id)
        if not nova_tributacao:
            return jsonify({'success': False, 'message': 'Tributação não encontrada'}), 404
        
        # Buscar vinculação atual
        vinculacao_atual = VinculacaoEmpresaTributacao.query.filter_by(
            empresa_id=empresa_id, ativo=True
        ).first()
        
        if not vinculacao_atual:
            return jsonify({'success': False, 'message': 'Vinculação atual não encontrada'}), 404
        
        # Verificar se já é a mesma tributação
        if vinculacao_atual.tributacao_id == nova_tributacao_id:
            return jsonify({'success': False, 'message': 'Empresa já está nesta tributação'}), 400
        
        # Iniciar transação
        db.session.begin()
        
        try:
            # 1. Desativar vinculação atual
            vinculacao_atual.ativo = False
            vinculacao_atual.data_fim = date.today()
            
            # 2. Desativar relacionamentos atuais
            relacionamentos_atuais = RelacionamentoTarefa.query.filter_by(
                empresa_id=empresa_id,
                versao_atual=True
            ).all()
            
            for rel in relacionamentos_atuais:
                rel.versao_atual = False
                rel.data_fim = date.today()
                rel.motivo_desativacao = motivo
            
            # 3. Criar nova vinculação
            nova_vinculacao = VinculacaoEmpresaTributacao(
                empresa_id=empresa_id,
                tributacao_id=nova_tributacao_id,
                data_inicio=date.today(),
                ativo=True
            )
            db.session.add(nova_vinculacao)
            db.session.flush()  # Para obter o ID
            
            # 4. Buscar tarefas da nova tributação
            tarefas_nova_tributacao = TarefaTributacao.query.filter_by(
                tributacao_id=nova_tributacao_id,
                ativo=True
            ).all()
            
            # 5. Criar novos relacionamentos
            novos_relacionamentos = 0
            for tt in tarefas_nova_tributacao:
                # Verificar se já existe relacionamento (para tarefas comuns)
                rel_existente = RelacionamentoTarefa.query.filter_by(
                    empresa_id=empresa_id,
                    tarefa_id=tt.tarefa_id,
                    versao_atual=False
                ).first()
                
                if rel_existente:
                    # Reativar relacionamento existente
                    rel_existente.versao_atual = True
                    rel_existente.vinculacao_id = nova_vinculacao.id
                    rel_existente.data_inicio = date.today()
                    rel_existente.data_fim = None
                    rel_existente.motivo_desativacao = None
                    
                    # Atualizar responsável se informado
                    if str(tt.tarefa_id) in responsaveis:
                        rel_existente.responsavel_id = responsaveis[str(tt.tarefa_id)]
                else:
                    # Criar novo relacionamento
                    responsavel_id = responsaveis.get(str(tt.tarefa_id))
                    
                    novo_rel = RelacionamentoTarefa(
                        empresa_id=empresa_id,
                        tarefa_id=tt.tarefa_id,
                        responsavel_id=responsavel_id,
                        vinculacao_id=nova_vinculacao.id,
                        status='ativa',
                        data_inicio=date.today(),
                        versao_atual=True
                    )
                    db.session.add(novo_rel)
                    novos_relacionamentos += 1
            
            # 6. Atualizar empresa
            empresa.tributacao_id = nova_tributacao_id
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': f'Tributação alterada com sucesso! {novos_relacionamentos} novas tarefas vinculadas.',
                'nova_tributacao': {
                    'id': nova_tributacao.id,
                    'nome': nova_tributacao.nome
                },
                'novos_relacionamentos': novos_relacionamentos
            })
            
        except Exception as e:
            db.session.rollback()
            raise e
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'}), 500


@bp.get('/api/responsaveis-padrao')
def api_responsaveis_padrao():
    """API para obter responsáveis padrão por setor e tributação"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'message': 'Usuário não autenticado'}), 401
        
        responsaveis = db.session.query(
            ConfiguracaoResponsavelPadrao, Setor, Tributacao, Usuario
        ).join(
            Setor, ConfiguracaoResponsavelPadrao.setor_id == Setor.id
        ).join(
            Tributacao, ConfiguracaoResponsavelPadrao.tributacao_id == Tributacao.id
        ).join(
            Usuario, ConfiguracaoResponsavelPadrao.responsavel_id == Usuario.id
        ).filter(
            ConfiguracaoResponsavelPadrao.ativo == True
        ).all()
        
        responsaveis_data = []
        for config, setor, tributacao, usuario in responsaveis:
            responsaveis_data.append({
                'id': config.id,
                'setor': {
                    'id': setor.id,
                    'nome': setor.nome
                },
                'tributacao': {
                    'id': tributacao.id,
                    'nome': tributacao.nome
                },
                'responsavel': {
                    'id': usuario.id,
                    'nome': usuario.nome
                }
            })
        
        return jsonify({
            'success': True,
            'responsaveis': responsaveis_data
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'}), 500


@bp.post('/api/responsaveis-padrao')
def api_criar_responsavel_padrao():
    """API para criar responsável padrão"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'message': 'Usuário não autenticado'}), 401
        
        data = request.get_json()
        setor_id = data.get('setor_id')
        tributacao_id = data.get('tributacao_id')
        responsavel_id = data.get('responsavel_id')
        
        if not all([setor_id, tributacao_id, responsavel_id]):
            return jsonify({'success': False, 'message': 'Dados incompletos'}), 400
        
        # Verificar se já existe configuração
        config_existente = ConfiguracaoResponsavelPadrao.query.filter_by(
            setor_id=setor_id,
            tributacao_id=tributacao_id,
            ativo=True
        ).first()
        
        if config_existente:
            # Atualizar existente
            config_existente.responsavel_id = responsavel_id
        else:
            # Criar novo
            nova_config = ConfiguracaoResponsavelPadrao(
                setor_id=setor_id,
                tributacao_id=tributacao_id,
                responsavel_id=responsavel_id
            )
            db.session.add(nova_config)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Responsável padrão configurado com sucesso!'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'}), 500
