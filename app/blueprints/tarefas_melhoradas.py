from flask import Blueprint, render_template, request, session, jsonify, redirect, url_for
from app.db import db
from app.models import (
    Empresa, Tributacao, Usuario, Tarefa, RelacionamentoTarefa, Setor,
    VinculacaoEmpresaTributacao, TarefaTributacao, ConfiguracaoResponsavelPadrao
)
from datetime import datetime, date
import json

bp = Blueprint('tarefas_melhoradas', __name__, url_prefix='/tarefas-melhoradas')


@bp.get('/standalone')
def gerente_tarefas_standalone():
    """Página STANDALONE de gerenciamento de tarefas (SEM base.html)"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return redirect(url_for('auth.login_page'))
        
        # Verificar se é gerente
        usuario = Usuario.query.get(user_id)
        if not usuario or usuario.tipo not in ['admin', 'gerente']:
            return redirect(url_for('auth.login_page'))
        
        # Buscar dados para a página
        setores = Setor.query.all()
        
        print(f"✅ Renderizando página standalone para {usuario.nome}")
        
        return render_template('gerente_tarefas.html',
                             usuario=usuario,
                             setores=setores)
        
    except Exception as e:
        print(f"Erro na página de tarefas standalone: {str(e)}")
        return redirect(url_for('auth.login_page'))


@bp.get('/nova')
def gerente_tarefas():
    """Nova página de gerenciamento de tarefas (LIMPA E FUNCIONAL)"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return redirect(url_for('auth.login_page'))
        
        # Verificar se é gerente
        usuario = Usuario.query.get(user_id)
        if not usuario or usuario.tipo not in ['admin', 'gerente']:
            return redirect(url_for('auth.login_page'))
        
        # Buscar dados para a página
        setores = Setor.query.all()
        
        return render_template('gerente_tarefas.html',
                             usuario=usuario,
                             setores=setores)
        
    except Exception as e:
        print(f"Erro na página de tarefas: {str(e)}")
        return redirect(url_for('auth.login_page'))


@bp.get('/')
def dashboard():
    """Dashboard principal do sistema melhorado de tarefas"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return redirect(url_for('auth.login_page'))
        
        # Verificar se é admin ou gerente
        usuario = Usuario.query.get(user_id)
        if not usuario or usuario.tipo not in ['admin', 'gerente']:
            return redirect(url_for('auth.login_page'))
        
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
        print(f"📋 Encontradas {len(tarefas)} tarefas para o usuário {usuario.nome} (tipo: {usuario.tipo})")
        
        tarefas_data = []
        for tarefa in tarefas:
            # Safely get setor name
            setor_nome = None
            try:
                if tarefa.setor:
                    setor_nome = tarefa.setor.nome
            except Exception as e:
                print(f"Erro ao acessar setor da tarefa {tarefa.id}: {e}")
                setor_nome = None
            
            tarefas_data.append({
                'id': tarefa.id,
                'nome': tarefa.nome,
                'tipo': tarefa.tipo,
                'descricao': tarefa.descricao,
                'tributacao': None,  # Será preenchido via TarefaTributacao se necessário
                'setor': setor_nome,
                'tarefa_comum': tarefa.tarefa_comum,
                'obrigatoria': True  # Por padrão, todas as tarefas são obrigatórias
            })
        
        print(f"📊 Retornando {len(tarefas_data)} tarefas para o frontend")
        return jsonify({'success': True, 'tarefas': tarefas_data})
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"❌ Erro na API /api/tarefas: {str(e)}")
        print(f"📋 Traceback: {error_details}")
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
        print(f"📝 Dados recebidos para criar tarefa: {data}")
        
        # Validar dados obrigatórios
        nome = data.get('nome', '').strip()
        tipo = data.get('tipo', '').strip()
        setor_id = data.get('setor_id')
        tributacao_id = data.get('tributacao_id')
        tarefa_comum = data.get('tarefa_comum', False)
        
        print(f"🔍 Validando dados:")
        print(f"  Nome: '{nome}' (len: {len(nome)})")
        print(f"  Tipo: '{tipo}' (len: {len(tipo)})")
        print(f"  Setor ID: {setor_id} (type: {type(setor_id)})")
        print(f"  Tributacao ID: {tributacao_id} (type: {type(tributacao_id)})")
        print(f"  Tarefa Comum: {tarefa_comum}")
        
        if not nome:
            return jsonify({'success': False, 'message': 'Nome da tarefa é obrigatório'}), 400
        if not tipo:
            return jsonify({'success': False, 'message': 'Tipo da tarefa é obrigatório'}), 400
        if not setor_id or setor_id == '':
            return jsonify({'success': False, 'message': 'Setor é obrigatório'}), 400
        
        # Se não for tarefa comum, tributação é obrigatória
        if not tarefa_comum and (not tributacao_id or tributacao_id == ''):
            return jsonify({'success': False, 'message': 'Tributação é obrigatória para tarefas específicas'}), 400
        
        # Converter IDs para int
        try:
            setor_id = int(setor_id)
            if tributacao_id and tributacao_id != '':
                tributacao_id = int(tributacao_id)
            else:
                tributacao_id = None
        except (ValueError, TypeError):
            return jsonify({'success': False, 'message': 'IDs de setor e tributação devem ser números válidos'}), 400
        
        # Criar nova tarefa
        print(f"🔧 Criando tarefa com dados validados: nome='{nome}', tipo='{tipo}', setor_id={setor_id}, tributacao_id={tributacao_id}")
        
        tarefa = Tarefa(
            nome=nome,
            tipo=tipo,
            descricao=data.get('descricao', ''),
            setor_id=setor_id,
            tributacao_id=tributacao_id,
            tarefa_comum=tarefa_comum
        )
        
        print(f"🔧 Adicionando tarefa ao banco de dados...")
        db.session.add(tarefa)
        
        print(f"🔧 Fazendo commit no banco de dados...")
        db.session.commit()
        
        print(f"✅ Tarefa criada com sucesso! ID: {tarefa.id}")
        
        # Verificar se a tarefa foi realmente salva
        tarefa_verificacao = Tarefa.query.get(tarefa.id)
        if tarefa_verificacao:
            print(f"✅ Tarefa confirmada no banco: {tarefa_verificacao.nome}")
            return jsonify({'success': True, 'message': 'Tarefa criada com sucesso!', 'tarefa_id': tarefa.id})
        else:
            print(f"❌ ERRO: Tarefa não foi salva no banco!")
            return jsonify({'success': False, 'message': 'Erro ao salvar tarefa no banco de dados'}), 500
        
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
    """API para buscar tarefas por nome com filtro opcional por empresa"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'message': 'Usuário não autenticado'}), 401
        
        # Verificar tipo de usuário
        usuario = Usuario.query.get(user_id)
        if not usuario or usuario.tipo not in ['admin', 'gerente']:
            return jsonify({'success': False, 'message': 'Acesso negado'}), 403
        
        query_param = request.args.get('q', '').strip()
        empresa_id = request.args.get('empresa_id', type=int)
        
        if len(query_param) < 2:
            return jsonify({'success': True, 'tarefas': []})
        
        # Buscar tarefas
        search_query = Tarefa.query.filter(Tarefa.nome.ilike(f'%{query_param}%'))
        
        # Filtrar por setor se for gerente
        if usuario.tipo == 'gerente':
            search_query = search_query.filter(Tarefa.setor_id == usuario.setor_id)
        
        # Se empresa_id for fornecido, filtrar tarefas já vinculadas para essa empresa
        if empresa_id:
            # Buscar tarefas já vinculadas para esta empresa
            tarefas_vinculadas = db.session.query(RelacionamentoTarefa.tarefa_id).filter(
                RelacionamentoTarefa.empresa_id == empresa_id,
                RelacionamentoTarefa.ativo == True
            ).subquery()
            
            # Excluir tarefas já vinculadas
            search_query = search_query.filter(~Tarefa.id.in_(
                db.session.query(tarefas_vinculadas.c.tarefa_id)
            ))
        
        tarefas = search_query.limit(10).all()
        
        tarefas_data = []
        for tarefa in tarefas:
            tarefas_data.append({
                'id': tarefa.id,
                'nome': tarefa.nome,
                'tipo': tarefa.tipo,
                'setor_nome': tarefa.setor.nome if tarefa.setor else 'N/A'
            })
        
        return jsonify({'success': True, 'tarefas': tarefas_data})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'}), 500


@bp.get('/api/empresas')
def api_empresas():
    """API para buscar empresas"""
    try:
        print(f"🔍 API empresas chamada - User ID: {session.get('user_id')}")
        
        user_id = session.get('user_id')
        if not user_id:
            print("❌ Usuário não autenticado")
            return jsonify({'success': False, 'message': 'Usuário não autenticado'}), 401
        
        # Verificar tipo de usuário
        usuario = Usuario.query.get(user_id)
        print(f"👤 Usuário encontrado: {usuario.nome if usuario else 'None'}, Tipo: {usuario.tipo if usuario else 'None'}")
        
        if not usuario or usuario.tipo not in ['admin', 'gerente']:
            print("❌ Acesso negado - tipo de usuário inválido")
            return jsonify({'success': False, 'message': 'Acesso negado'}), 403
        
        search = request.args.get('search', '').strip()
        print(f"🔍 Busca: '{search}'")
        
        # Buscar empresas ativas
        empresas_query = Empresa.query.filter(Empresa.ativo == True)
        
        if search:
            empresas_query = empresas_query.filter(Empresa.nome.ilike(f'%{search}%'))
        
        empresas = empresas_query.limit(20).all()
        print(f"📊 Empresas encontradas: {len(empresas)}")
        
        empresas_data = []
        for empresa in empresas:
            empresas_data.append({
                'id': empresa.id,
                'nome': empresa.nome,
                'codigo': empresa.codigo
            })
        
        print(f"✅ Retornando {len(empresas_data)} empresas")
        return jsonify({
            'success': True,
            'empresas': empresas_data
        })
        
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
