from flask import Blueprint, render_template, request, session, jsonify
from app.db import db
from app.models import (
    Setor, Empresa, Usuario, Tarefa, RelacionamentoTarefa, Periodo, Tributacao, 
    PeriodoExecucao, HistoricoMudancaTributacao, MudancaTributacaoPendente,
    VinculacaoEmpresaTributacao, TarefaTributacao
)
from app.utils import (
    get_previous_period, get_previous_period_label, convert_period_to_label, 
    validate_period_format, should_show_task_by_type
)
from datetime import datetime, date
import re

bp = Blueprint('gerenciamento', __name__, url_prefix='/gerenciamento')


# Funções consolidadas em app/utils.py


@bp.get('')
@bp.get('/')
def return_page():
    """Página principal do painel do gerente"""
    try:
        # Parâmetros da requisição
        setor_atual = request.args.get('setor_id')
        if setor_atual:
            setor_atual = int(setor_atual)
        periodo_input = request.args.get('periodo', get_previous_period())
        empresa_atual = request.args.get('empresa_id')
        if empresa_atual:
            empresa_atual = int(empresa_atual)
        empresa_ids = request.args.get('empresa_ids', '')
        colaborador_id = request.args.get('colaborador_id')
        if colaborador_id:
            colaborador_id = int(colaborador_id)
        tarefa_id = request.args.get('tarefa_id')
        if tarefa_id:
            tarefa_id = int(tarefa_id)
        user_id = session.get('user_id')
        
        # Processar múltiplas empresas
        empresa_ids_list = []
        if empresa_ids:
            try:
                empresa_ids_list = [int(id.strip()) for id in empresa_ids.split(',') if id.strip().isdigit()]
            except ValueError:
                empresa_ids_list = []
        
        # Validar período
        if not validate_period_format(periodo_input):
            periodo_input = '08/2025'  # Valor padrão
        
        periodo_atual = convert_period_to_label(periodo_input)
        
        # Buscar dados do usuário
        usuario = Usuario.query.get(user_id) if user_id else None
        user_setor_id = usuario.setor_id if usuario else None
        user_setor_nome = None
        if usuario and user_setor_id:
            setor = Setor.query.get(user_setor_id)
            user_setor_nome = setor.nome if setor else 'N/A'
        
        # Buscar todas as empresas que têm tarefas
        empresas_query = db.session.query(Empresa).join(
            RelacionamentoTarefa, RelacionamentoTarefa.empresa_id == Empresa.id
        ).join(
            Tarefa, RelacionamentoTarefa.tarefa_id == Tarefa.id
        ).filter(
            Empresa.ativo == True,
            RelacionamentoTarefa.status == 'ativa'
        )
        
        # Filtrar empresas por setor do gerente (se for gerente)
        if usuario and usuario.tipo == 'gerente' and usuario.setor_id:
            empresas_query = empresas_query.filter(Tarefa.setor_id == usuario.setor_id)
        
        empresas_query = empresas_query.distinct().order_by(Empresa.nome)
        
        empresas = empresas_query.all()
        
        # Converter empresas para formato JSON-friendly
        empresas_json = []
        for empresa in empresas:
            empresas_json.append({
                'id': empresa.id,
                'nome': empresa.nome,
                'codigo': empresa.codigo
            })
        
        # Buscar períodos para o período selecionado
        q = db.session.query(Periodo, RelacionamentoTarefa, Tarefa, Empresa, Usuario).join(
            RelacionamentoTarefa, Periodo.relacionamento_tarefa_id == RelacionamentoTarefa.id
        ).join(
            Tarefa, RelacionamentoTarefa.tarefa_id == Tarefa.id
        ).join(
            Empresa, RelacionamentoTarefa.empresa_id == Empresa.id
        ).outerjoin(
            Usuario, RelacionamentoTarefa.responsavel_id == Usuario.id
        ).filter(
            Periodo.periodo_label == periodo_atual,
            Empresa.ativo == True,
            RelacionamentoTarefa.status == 'ativa'
        )
        
        # Filtrar por setor do gerente (se for gerente)
        if usuario and usuario.tipo == 'gerente' and usuario.setor_id:
            q = q.filter(Tarefa.setor_id == usuario.setor_id)
        
        # Filtrar por empresa se selecionada
        if empresa_atual:
            q = q.filter(Empresa.id == empresa_atual)
        
        # Executar query e processar resultados
        resultados_brutos = q.all()
        
        # Aplicar filtragem inteligente por tipo de tarefa
        resultados = []
        for p, rel, tar, emp, usu in resultados_brutos:
            # Excluir tarefas anuais (são tratadas separadamente)
            if tar.tipo == 'Anual':
                continue
            
            # Para tarefas trimestrais, aplicar filtragem inteligente
            if tar.tipo == 'Trimestral':
                if not _should_show_task_by_type(tar.tipo, periodo_atual, p.periodo_label):
                    continue
            else:
                # Para tarefas mensais, aplicar filtro de período normalmente
                if p.periodo_label != periodo_atual:
                    continue
            
            resultados.append((p, rel, tar, emp, usu))
        
        # Inicializar estruturas de dados
        resumo = {"pendentes": 0, "fazendo": 0, "concluidas": 0}
        empresas_resumo_map = {}
        responsaveis_tarefas = []
        
        # Processar cada resultado
        for p, rel, tar, emp, usu in resultados:
            status = p.status or 'pendente'
            
            # Contar para resumo geral
            if status == 'pendente':
                resumo['pendentes'] += 1
            elif status in ['concluida', 'retificada']:
                resumo['concluidas'] += 1
            else:
                resumo['fazendo'] += 1

            # Contar para resumo por empresa
            key = emp.id
            if key not in empresas_resumo_map:
                empresas_resumo_map[key] = {
                    "nome": emp.nome, 
                    "pendentes": 0, 
                    "fazendo": 0, 
                    "concluidas": 0
                }
            
            if status == 'pendente':
                empresas_resumo_map[key]['pendentes'] += 1
            elif status in ['concluida', 'retificada']:
                empresas_resumo_map[key]['concluidas'] += 1
            else:
                empresas_resumo_map[key]['fazendo'] += 1
            
            # Adicionar à lista de responsáveis
            responsaveis_tarefas.append({
                "usuario_nome": (usu.nome if usu else 'Não atribuído'),
                "empresa_nome": emp.nome,
                "tarefa_nome": tar.nome,
                "status": status,
                "periodo_label": p.periodo_label
            })
        
        # Converter map para lista
        empresas_resumo = list(empresas_resumo_map.values())

        # Ordenar por nome da empresa
        empresas_resumo.sort(key=lambda x: x['nome'])
        responsaveis_tarefas.sort(key=lambda x: (x['empresa_nome'], x['tarefa_nome']))
        
        # Calcular taxa de conclusão
        total_tarefas = resumo['pendentes'] + resumo['fazendo'] + resumo['concluidas']
        taxa_conclusao = (resumo['concluidas'] / total_tarefas * 100) if total_tarefas > 0 else 0
        
        # Debug: Log dos dados encontrados
        print(f"DEBUG GERENCIAMENTO - Período: {periodo_atual}, Empresa: {empresa_atual}")
        print(f"DEBUG GERENCIAMENTO - Resultados encontrados: {len(resultados)}")
        print(f"DEBUG GERENCIAMENTO - Resumo: {resumo}")
        print(f"DEBUG GERENCIAMENTO - Empresas resumo: {len(empresas_resumo)}")
        print(f"DEBUG GERENCIAMENTO - Responsáveis: {len(responsaveis_tarefas)}")

        # Buscar mudanças de tributação pendentes para notificação (filtradas por setor se for gerente)
        if usuario and usuario.tipo == 'gerente' and usuario.setor_id:
            # Gerente: apenas mudanças que têm tarefas do seu setor sem responsável
            mudancas_ids = db.session.query(MudancaTributacaoPendente.id).join(
                RelacionamentoTarefa, RelacionamentoTarefa.empresa_id == MudancaTributacaoPendente.empresa_id
            ).join(
                Tarefa, RelacionamentoTarefa.tarefa_id == Tarefa.id
            ).filter(
                MudancaTributacaoPendente.status.in_(['pendente', 'em_revisao']),
                RelacionamentoTarefa.responsavel_id.is_(None),
                RelacionamentoTarefa.versao_atual == True,
                Tarefa.setor_id == usuario.setor_id
            ).distinct()
            
            mudanca_ids_list = [m[0] for m in mudancas_ids.all()]
            mudancas_pendentes = len(mudanca_ids_list) if mudanca_ids_list else 0
        else:
            # Admin: todas as mudanças pendentes
            mudancas_pendentes = MudancaTributacaoPendente.query.filter(
                MudancaTributacaoPendente.status.in_(['pendente', 'em_revisao'])
            ).count()
        
        return render_template(
            'gerenciamento.html',
            periodo_atual=periodo_input,
            empresas=empresas_json,
            empresa_atual=empresa_atual,
            resumo=resumo,
            taxa_conclusao=taxa_conclusao,
            empresas_resumo=empresas_resumo,
            responsaveis_tarefas=responsaveis_tarefas,
            user_setor_nome=user_setor_nome or 'Todos os Setores',
            mudancas_pendentes=mudancas_pendentes,
        )
        
    except Exception as e:
        print(f"ERRO no gerenciamento: {str(e)}")
        # Retornar página com dados vazios em caso de erro
        return render_template(
            'gerenciamento.html',
            periodo_atual='08/2025',
            empresas=[],
            empresa_atual=None,
            resumo={"pendentes": 0, "fazendo": 0, "concluidas": 0},
            taxa_conclusao=0,
            empresas_resumo=[],
            responsaveis_tarefas=[],
            user_setor_nome='Todos os Setores',
        )


@bp.get('/api/empresas')
def api_empresas():
    """API para buscar empresas para o painel do gerente"""
    try:
        search = request.args.get('search', '').strip()
        user_id = session.get('user_id')
        usuario = Usuario.query.get(user_id) if user_id else None
        
        # Buscar empresas que têm tarefas ativas
        query = db.session.query(Empresa).join(
            RelacionamentoTarefa, RelacionamentoTarefa.empresa_id == Empresa.id
        ).join(
            Tarefa, RelacionamentoTarefa.tarefa_id == Tarefa.id
        ).filter(
            Empresa.ativo == True,
            RelacionamentoTarefa.status == 'ativa'
        )
        
        # Filtrar por setor do gerente (se for gerente)
        if usuario and usuario.tipo == 'gerente' and usuario.setor_id:
            query = query.filter(Tarefa.setor_id == usuario.setor_id)
        
        query = query.distinct()
        
        if search:
            query = query.filter(
                (Empresa.nome.contains(search)) | 
                (Empresa.codigo.contains(search))
            )
        
        empresas = query.order_by(Empresa.nome).limit(50).all()
        
        empresas_data = []
        for empresa in empresas:
            empresas_data.append({
                'id': empresa.id,
                'nome': empresa.nome,
                'codigo': empresa.codigo
            })
        
        return jsonify({
            'success': True,
            'empresas': empresas_data
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro ao buscar empresas: {str(e)}'
        }), 500


@bp.get('/api/colaboradores')
def api_colaboradores():
    """API para buscar colaboradores para o painel do gerente"""
    try:
        search = request.args.get('search', '').strip()
        
        # Buscar usuários que são colaboradores
        query = db.session.query(Usuario).filter(Usuario.tipo == 'normal')
        
        if search:
            query = query.filter(
                (Usuario.nome.contains(search)) | 
                (Usuario.login.contains(search))
            )
        
        colaboradores = query.order_by(Usuario.nome).limit(50).all()
        
        colaboradores_data = []
        for colaborador in colaboradores:
            colaboradores_data.append({
                'id': colaborador.id,
                'nome': colaborador.nome,
                'login': colaborador.login,
                'tipo': 'Colaborador'
            })
        
        return jsonify({
            'success': True,
            'usuarios': colaboradores_data,  # Retornar como 'usuarios' para consistência
            'colaboradores': colaboradores_data  # Manter 'colaboradores' para compatibilidade
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro ao buscar colaboradores: {str(e)}'
        }), 500


@bp.get('/api/tarefas')
def api_tarefas():
    """API para buscar tarefas para o painel do gerente"""
    try:
        search = request.args.get('search', '').strip()
        user_id = session.get('user_id')
        usuario = Usuario.query.get(user_id) if user_id else None
        
        # Buscar tarefas
        query = db.session.query(Tarefa)
        
        # Filtrar por setor do gerente (se for gerente)
        if usuario and usuario.tipo == 'gerente' and usuario.setor_id:
            query = query.filter(Tarefa.setor_id == usuario.setor_id)
        
        if search:
            query = query.filter(
                (Tarefa.nome.contains(search)) | 
                (Tarefa.tipo.contains(search))
            )
        
        tarefas = query.order_by(Tarefa.nome).limit(50).all()
        
        tarefas_data = []
        for tarefa in tarefas:
            tarefas_data.append({
                'id': tarefa.id,
                'nome': tarefa.nome,
                'tipo': tarefa.tipo,
                'setor_id': tarefa.setor_id
            })
        
        return jsonify({
            'success': True,
            'tarefas': tarefas_data
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro ao buscar tarefas: {str(e)}'
        }), 500


@bp.get('/api/resumo')
def api_resumo():
    """API para buscar resumo de dados por período e empresa"""
    try:
        periodo_input = request.args.get('periodo', '08/2025')
        empresa_id = request.args.get('empresa_id')
        if empresa_id:
            empresa_id = int(empresa_id)
        empresa_ids = request.args.get('empresa_ids', '')
        colaborador_id = request.args.get('colaborador_id')
        if colaborador_id:
            colaborador_id = int(colaborador_id)
        tarefa_id = request.args.get('tarefa_id')
        if tarefa_id:
            tarefa_id = int(tarefa_id)
        
        # Validar período
        if not validate_period_format(periodo_input):
            return jsonify({
                'success': False,
                'message': 'Formato de período inválido. Use MM/AAAA'
            }), 400
        
        periodo_atual = convert_period_to_label(periodo_input)
        
        # Buscar dados
        q = db.session.query(Periodo, RelacionamentoTarefa, Tarefa, Empresa, Usuario).join(
            RelacionamentoTarefa, Periodo.relacionamento_tarefa_id == RelacionamentoTarefa.id
        ).join(
            Tarefa, RelacionamentoTarefa.tarefa_id == Tarefa.id
        ).join(
            Empresa, RelacionamentoTarefa.empresa_id == Empresa.id
        ).outerjoin(
            Usuario, RelacionamentoTarefa.responsavel_id == Usuario.id
        ).filter(
            Empresa.ativo == True,
            RelacionamentoTarefa.status == 'ativa'
        )
        
        # Filtrar por empresa(s) se especificada(s)
        if empresa_ids:
            empresa_id_list = [int(id.strip()) for id in empresa_ids.split(',') if id.strip()]
            if empresa_id_list:
                q = q.filter(Empresa.id.in_(empresa_id_list))
        elif empresa_id:
            q = q.filter(Empresa.id == empresa_id)
        
        # Filtrar por colaborador se especificado
        if colaborador_id:
            q = q.filter(Usuario.id == colaborador_id)
        
        # Filtrar por tarefa se especificada
        if tarefa_id:
            q = q.filter(Tarefa.id == tarefa_id)
        
        # Filtrar por setor do gerente (se for gerente)
        user_id = session.get('user_id')
        usuario = Usuario.query.get(user_id) if user_id else None
        if usuario and usuario.tipo == 'gerente' and usuario.setor_id:
            q = q.filter(Tarefa.setor_id == usuario.setor_id)
        
        # Executar query
        resultados_brutos = q.all()
        
        # Aplicar filtragem inteligente por tipo de tarefa
        resultados = []
        for p, rel, tar, emp, usu in resultados_brutos:
            # Excluir tarefas anuais (são tratadas separadamente)
            if tar.tipo == 'Anual':
                continue
            
            # Para tarefas trimestrais, aplicar filtragem inteligente
            if tar.tipo == 'Trimestral':
                if not _should_show_task_by_type(tar.tipo, periodo_atual, p.periodo_label):
                    continue
            else:
                # Para tarefas mensais, aplicar filtro de período normalmente
                if p.periodo_label != periodo_atual:
                    continue
            
            resultados.append((p, rel, tar, emp, usu))
        
        # Processar resultados
        resumo = {"pendentes": 0, "fazendo": 0, "concluidas": 0}
        empresas_resumo_map = {}
        responsaveis_tarefas = []
        
        for p, rel, tar, emp, usu in resultados:
            status = p.status or 'pendente'
            
            if status == 'pendente':
                resumo['pendentes'] += 1
            elif status in ['concluida', 'retificada']:
                resumo['concluidas'] += 1
            else:
                resumo['fazendo'] += 1
            
            # Resumo por empresa
            key = emp.id
            if key not in empresas_resumo_map:
                empresas_resumo_map[key] = {
                    "nome": emp.nome, 
                    "pendentes": 0, 
                    "fazendo": 0, 
                    "concluidas": 0
                }
            
            if status == 'pendente':
                empresas_resumo_map[key]['pendentes'] += 1
            elif status in ['concluida', 'retificada']:
                empresas_resumo_map[key]['concluidas'] += 1
            else:
                empresas_resumo_map[key]['fazendo'] += 1
            
            # Lista de responsáveis
            contador_retificacoes = getattr(p, 'contador_retificacoes', 0) if hasattr(p, 'contador_retificacoes') else 0
            
            # Converter período de AAAA-MM para MM/AAAA
            if p.periodo_label and len(p.periodo_label) >= 7:
                ano = p.periodo_label[:4]  # AAAA
                mes = p.periodo_label[5:7]  # MM
                periodo_brasileiro = f"{mes}/{ano}"
            else:
                periodo_brasileiro = p.periodo_label or ''
            
            responsaveis_tarefas.append({
                "usuario_nome": (usu.nome if usu else 'Não atribuído'),
                "empresa_nome": emp.nome,
                "tarefa_nome": tar.nome,
                "status": status,
                "periodo_label": periodo_brasileiro,
                "contador_retificacoes": contador_retificacoes
            })
        
        # Calcular taxa de conclusão para cada empresa
        for empresa in empresas_resumo_map.values():
            total = empresa['pendentes'] + empresa['fazendo'] + empresa['concluidas']
            empresa['taxa_conclusao'] = (empresa['concluidas'] / total * 100) if total > 0 else 0
        
        empresas_resumo = list(empresas_resumo_map.values())
        empresas_resumo.sort(key=lambda x: x['nome'])
        responsaveis_tarefas.sort(key=lambda x: (x['empresa_nome'], x['tarefa_nome']))
        
        # Calcular taxa de conclusão
        total_tarefas = len(resultados)
        taxa_conclusao = (resumo['concluidas'] / total_tarefas * 100) if total_tarefas > 0 else 0
        
        return jsonify({
            'success': True,
            'resumo': resumo,
            'taxa_conclusao': taxa_conclusao,
            'empresas_resumo': empresas_resumo,
            'responsaveis_tarefas': responsaveis_tarefas,
            'periodo': periodo_atual,
            'total_encontrados': len(resultados)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro ao buscar resumo: {str(e)}'
        }), 500


@bp.get('/api/tarefas-anuais')
def api_tarefas_anuais():
    """API para buscar tarefas anuais do painel do gerente"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'message': 'Usuário não autenticado'}), 401
        
        # Buscar dados do usuário
        usuario = Usuario.query.get(user_id)
        user_tipo = usuario.tipo if usuario else 'normal'
        user_setor_id = usuario.setor_id if usuario else None
        
        # Buscar tarefas anuais relacionadas ao setor do gerente
        query = db.session.query(Periodo, RelacionamentoTarefa, Tarefa, Empresa, Usuario).join(
            RelacionamentoTarefa, Periodo.relacionamento_tarefa_id == RelacionamentoTarefa.id
        ).join(
            Tarefa, RelacionamentoTarefa.tarefa_id == Tarefa.id
        ).join(
            Empresa, RelacionamentoTarefa.empresa_id == Empresa.id
        ).outerjoin(
            Usuario, RelacionamentoTarefa.responsavel_id == Usuario.id
        ).filter(
            Tarefa.tipo == 'Anual',
            Empresa.ativo == True,
            RelacionamentoTarefa.status == 'ativa'
        )
        
        # Aplicar filtro de setor apenas para gerentes
        if user_tipo == 'gerente' and user_setor_id:
            query = query.filter(Tarefa.setor_id == usuario.setor_id)
        
        tarefas_anuais = []
        for p, rel, tar, emp, usu in query.all():
            tarefas_anuais.append({
                "periodo_id": p.id,
                "usuario_nome": (usu.nome if usu else 'Não atribuído'),
                "empresa_nome": emp.nome,
                "tarefa_nome": tar.nome,
                "status": p.status or 'pendente',
                "periodo_label": p.periodo_label,
                "contador_retificacoes": p.contador_retificacoes or 0
            })
        
        return jsonify({'success': True, 'tarefas_anuais': tarefas_anuais})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro ao buscar tarefas anuais: {str(e)}'}), 500


# ===== NOVAS APIs PARA FUNCIONALIDADES DO GERENTE =====

@bp.get('/api/setores')
def api_setores():
    """API para buscar setores"""
    try:
        setores = Setor.query.all()
        return jsonify({
            'success': True,
            'setores': [{'id': s.id, 'nome': s.nome} for s in setores]
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro ao buscar setores: {str(e)}'}), 500


@bp.get('/api/tributacoes')
def api_tributacoes():
    """API para buscar tributações"""
    try:
        tributacoes = Tributacao.query.all()
        return jsonify({
            'success': True,
            'tributacoes': [{'id': t.id, 'nome': t.nome} for t in tributacoes]
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro ao buscar tributações: {str(e)}'}), 500


@bp.post('/api/tarefas')
def api_criar_tarefa():
    """API para criar nova tarefa"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'message': 'Usuário não autenticado'}), 401
        
        usuario = Usuario.query.get(user_id)
        if not usuario or usuario.tipo not in ['admin', 'gerente']:
            return jsonify({'success': False, 'message': 'Acesso negado'}), 403
        
        data = request.get_json()
        nome = data.get('nome')
        tipo = data.get('tipo')
        setor_id = data.get('setor_id')
        tributacao_id = data.get('tributacao_id')
        descricao = data.get('descricao', '')
        tarefa_comum = data.get('tarefa_comum', False)
        
        if not nome or not tipo or not setor_id:
            return jsonify({'success': False, 'message': 'Campos obrigatórios não fornecidos'}), 400
        
        # Criar nova tarefa
        tarefa = Tarefa(
            nome=nome,
            tipo=tipo,
            setor_id=int(setor_id),
            tributacao_id=int(tributacao_id) if tributacao_id else None,
            descricao=descricao,
            tarefa_comum=tarefa_comum
        )
        
        db.session.add(tarefa)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Tarefa criada com sucesso!',
            'tarefa_id': tarefa.id
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Erro ao criar tarefa: {str(e)}'}), 500


@bp.post('/api/periodos')
def api_criar_periodo():
    """API para criar período mensal"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'message': 'Usuário não autenticado'}), 401
        
        usuario = Usuario.query.get(user_id)
        if not usuario or usuario.tipo not in ['admin', 'gerente']:
            return jsonify({'success': False, 'message': 'Acesso negado'}), 403
        
        data = request.get_json()
        empresa_id = data.get('empresa_id')
        ano = data.get('ano')
        mes = data.get('mes')
        
        if not empresa_id or not ano or not mes:
            return jsonify({'success': False, 'message': 'Dados obrigatórios não fornecidos'}), 400
        
        # Verificar se já existe período
        periodo_existente = PeriodoExecucao.query.filter_by(
            empresa_id=empresa_id,
            ano=ano,
            mes=mes
        ).first()
        
        if periodo_existente:
            return jsonify({'success': False, 'message': 'Período já existe para esta empresa'}), 400
        
        # Calcular datas do período
        from datetime import date
        data_inicio = date(ano, mes, 1)
        if mes == 12:
            data_fim = date(ano + 1, 1, 1)
        else:
            data_fim = date(ano, mes + 1, 1)
        
        periodo = PeriodoExecucao(
            empresa_id=empresa_id,
            ano=ano,
            mes=mes,
            data_inicio=data_inicio,
            data_fim=data_fim,
            status='ativo'
        )
        
        db.session.add(periodo)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Período criado com sucesso!',
            'periodo_id': periodo.id
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Erro ao criar período: {str(e)}'}), 500


@bp.post('/api/vincular-responsavel')
def api_vincular_responsavel():
    """API para vincular responsável a tarefas"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'message': 'Usuário não autenticado'}), 401
        
        usuario = Usuario.query.get(user_id)
        if not usuario or usuario.tipo not in ['admin', 'gerente']:
            return jsonify({'success': False, 'message': 'Acesso negado'}), 403
        
        data = request.get_json()
        empresa_id = data.get('empresa_id')
        responsavel_id = data.get('responsavel_id')
        tarefa_ids = data.get('tarefa_ids', [])
        
        if not empresa_id or not responsavel_id or not tarefa_ids:
            return jsonify({'success': False, 'message': 'Dados obrigatórios não fornecidos'}), 400
        
        vinculacoes_criadas = 0
        
        for tarefa_id in tarefa_ids:
            # Verificar se já existe vinculação
            vinculacao_existente = RelacionamentoTarefa.query.filter_by(
                empresa_id=empresa_id,
                tarefa_id=tarefa_id,
                responsavel_id=responsavel_id,
                status='ativa'
            ).first()
            
            if not vinculacao_existente:
                vinculacao = RelacionamentoTarefa(
                    empresa_id=empresa_id,
                    tarefa_id=tarefa_id,
                    responsavel_id=responsavel_id,
                    status='ativa'
                )
                
                db.session.add(vinculacao)
                vinculacoes_criadas += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'{vinculacoes_criadas} vinculações criadas com sucesso!',
            'vinculacoes_criadas': vinculacoes_criadas
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Erro ao vincular responsável: {str(e)}'}), 500


# ===== APIs PARA GERENCIAMENTO DE TRIBUTAÇÃO =====

@bp.get('/api/empresas-tributacao')
def api_empresas_tributacao():
    """API para buscar empresas com mudança de tributação"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'message': 'Usuário não autenticado'}), 401
        
        usuario = Usuario.query.get(user_id)
        if not usuario or usuario.tipo not in ['admin', 'gerente']:
            return jsonify({'success': False, 'message': 'Acesso negado'}), 403
        
        # Por enquanto, retornar lista vazia pois não há mudanças de tributação pendentes
        # Quando houver mudanças reais, implementar a busca abaixo:
        empresas_data = []
        
        # Código comentado para quando houver dados reais:
        # empresas = db.session.query(Empresa).join(
        #     HistoricoMudancaTributacao, HistoricoMudancaTributacao.empresa_id == Empresa.id
        # ).filter(
        #     Empresa.ativo == True,
        #     HistoricoMudancaTributacao.status == 'pendente'
        # ).distinct().all()
        
        return jsonify({
            'success': True,
            'empresas': empresas_data
        })
        
    except Exception as e:
        print(f"Erro na API empresas-tributacao: {str(e)}")
        return jsonify({'success': False, 'message': f'Erro ao buscar empresas: {str(e)}'}), 500


@bp.get('/api/tarefas-empresa/<int:empresa_id>')
def api_tarefas_empresa(empresa_id):
    """API para buscar tarefas de uma empresa específica"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'message': 'Usuário não autenticado'}), 401
        
        usuario = Usuario.query.get(user_id)
        if not usuario or usuario.tipo not in ['admin', 'gerente']:
            return jsonify({'success': False, 'message': 'Acesso negado'}), 403
        
        # Buscar tarefas vinculadas à empresa
        tarefas = db.session.query(Tarefa, RelacionamentoTarefa).join(
            RelacionamentoTarefa, RelacionamentoTarefa.tarefa_id == Tarefa.id
        ).filter(
            RelacionamentoTarefa.empresa_id == empresa_id,
            RelacionamentoTarefa.status == 'ativa'
        ).all()
        
        tarefas_data = []
        for tarefa, rel in tarefas:
            # Buscar informação da tributação
            tributacao_nome = 'Sem tributação específica'
            if tarefa.tributacao_id:
                tributacao = Tributacao.query.get(tarefa.tributacao_id)
                if tributacao:
                    tributacao_nome = tributacao.nome
            
            tarefas_data.append({
                'id': tarefa.id,
                'nome': tarefa.nome,
                'tipo': tarefa.tipo,
                'tributacao': tributacao_nome,
                'relacionamento_id': rel.id
            })
        
        return jsonify({
            'success': True,
            'tarefas': tarefas_data
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro ao buscar tarefas: {str(e)}'}), 500


@bp.post('/api/reconfigurar-tributacao')
def api_reconfigurar_tributacao():
    """API para reconfigurar tarefas após mudança de tributação"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'message': 'Usuário não autenticado'}), 401
        
        usuario = Usuario.query.get(user_id)
        if not usuario or usuario.tipo not in ['admin', 'gerente']:
            return jsonify({'success': False, 'message': 'Acesso negado'}), 403
        
        data = request.get_json()
        empresa_id = data.get('empresa_id')
        tarefa_ids = data.get('tarefa_ids', [])
        
        if not empresa_id or not tarefa_ids:
            return jsonify({'success': False, 'message': 'Dados obrigatórios não fornecidos'}), 400
        
        # Buscar histórico de mudança de tributação
        historico = HistoricoMudancaTributacao.query.filter_by(
            empresa_id=empresa_id,
            status='pendente'
        ).order_by(HistoricoMudancaTributacao.data_mudanca.desc()).first()
        
        if not historico:
            return jsonify({'success': False, 'message': 'Não há mudança de tributação pendente'}), 400
        
        reconfiguradas = 0
        
        for tarefa_id in tarefa_ids:
            # Buscar relacionamento da tarefa
            rel = RelacionamentoTarefa.query.filter_by(
                empresa_id=empresa_id,
                tarefa_id=tarefa_id,
                status='ativa'
            ).first()
            
            if rel:
                # Desativar relacionamento atual
                rel.status = 'desativada'
                rel.motivo_desativacao = f'Mudança de tributação - {historico.data_mudanca.strftime("%d/%m/%Y")}'
                
                # Criar novo relacionamento se a tarefa se aplica à nova tributação
                tarefa = Tarefa.query.get(tarefa_id)
                if tarefa and (not tarefa.tributacao_id or tarefa.tributacao_id == historico.tributacao_nova_id or tarefa.tarefa_comum):
                    novo_rel = RelacionamentoTarefa(
                        empresa_id=empresa_id,
                        tarefa_id=tarefa_id,
                        responsavel_id=rel.responsavel_id,  # Manter mesmo responsável
                        status='ativa',
                        vinculacao_id=rel.vinculacao_id,
                        data_inicio=historico.data_mudanca,
                        versao_atual=True
                    )
                    db.session.add(novo_rel)
                    reconfiguradas += 1
        
        # Marcar histórico como processado
        historico.status = 'processada'
        historico.data_processamento = datetime.now()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'{reconfiguradas} tarefas reconfiguradas com sucesso!',
            'reconfiguradas': reconfiguradas
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Erro ao reconfigurar tributação: {str(e)}'}), 500


@bp.get('/api/usuarios-busca')
def api_usuarios_busca():
    """API para busca avançada de usuários"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'message': 'Usuário não autenticado'}), 401
        
        usuario = Usuario.query.get(user_id)
        if not usuario or usuario.tipo not in ['admin', 'gerente']:
            return jsonify({'success': False, 'message': 'Acesso negado'}), 403
        
        search = request.args.get('search', '').strip()
        
        # Buscar usuários baseado no tipo do usuário logado
        if usuario.tipo == 'admin':
            # Admin vê todos os usuários
            query = Usuario.query.filter(Usuario.ativo == True)
        else:
            # Gerente vê apenas usuários do seu setor
            query = Usuario.query.filter(
                Usuario.ativo == True,
                Usuario.setor_id == usuario.setor_id
            )
        
        if search:
            query = query.filter(
                (Usuario.nome.contains(search)) |
                (Usuario.login.contains(search))
            )
        
        usuarios = query.order_by(Usuario.nome).limit(50).all()
        
        usuarios_data = []
        for user in usuarios:
            usuarios_data.append({
                'id': user.id,
                'nome': user.nome,
                'login': user.login,
                'tipo': user.tipo,
                'setor': user.setor.nome if user.setor else 'Sem setor'
            })
        
        return jsonify({
            'success': True,
            'usuarios': usuarios_data
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro ao buscar usuários: {str(e)}'}), 500


# ===== PAINEL DE MUDANÇAS DE TRIBUTAÇÃO =====

@bp.get('/mudancas-tributacao')
def mudancas_tributacao():
    """Painel do gerente para revisar mudanças de tributação pendentes"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return redirect(url_for('auth.login_page'))
        
        # Verificar se é gerente ou admin
        usuario = Usuario.query.get(user_id)
        if not usuario or usuario.tipo not in ['admin', 'gerente']:
            return redirect(url_for('auth.login_page'))
        
        # Buscar mudanças pendentes - usar SQL puro para evitar conflito de JOINs
        from sqlalchemy import text
        
        # Construir query SQL pura
        if usuario.tipo == 'gerente' and usuario.setor_id:
            # Para gerente: filtrar apenas empresas com tarefas do seu setor
            sql = text("""
                SELECT DISTINCT m.id, m.empresa_id, m.tributacao_anterior_id, m.tributacao_nova_id,
                       m.data_mudanca, m.motivo, m.status, m.criado_em
                FROM mudancas_tributacao_pendentes m
                WHERE m.status IN ('pendente', 'em_revisao')
                  AND EXISTS (
                      SELECT 1 FROM relacionamento_tarefas rt
                      INNER JOIN tarefas t ON rt.tarefa_id = t.id
                      WHERE rt.empresa_id = m.empresa_id
                        AND rt.responsavel_id IS NULL
                        AND rt.versao_atual = 1
                        AND t.setor_id = :setor_id
                  )
                ORDER BY m.criado_em DESC
            """)
            result = db.session.execute(sql, {'setor_id': usuario.setor_id})
        else:
            # Para admin: todas as mudanças pendentes
            sql = text("""
                SELECT id, empresa_id, tributacao_anterior_id, tributacao_nova_id,
                       data_mudanca, motivo, status, criado_em
                FROM mudancas_tributacao_pendentes
                WHERE status IN ('pendente', 'em_revisao')
                ORDER BY criado_em DESC
            """)
            result = db.session.execute(sql)
        
        # Converter resultados em objetos simples
        class MudancaSimples:
            def __init__(self, row):
                self.id = row[0]
                self.empresa_id = row[1]
                self.tributacao_anterior_id = row[2]
                self.tributacao_nova_id = row[3]
                self.data_mudanca = row[4]
                self.motivo = row[5]
                self.status = row[6]
                self.criado_em = row[7]
        
        mudancas = [MudancaSimples(row) for row in result]
        
        # Buscar tarefas sem responsável para cada mudança
        mudancas_data = []
        for mudanca in mudancas:
            # Buscar empresa separadamente
            empresa = Empresa.query.get(mudanca.empresa_id)
            
            # Buscar tributações separadamente para evitar conflito de JOIN
            trib_anterior = None
            trib_nova = None
            
            if mudanca.tributacao_anterior_id:
                trib_anterior = Tributacao.query.get(mudanca.tributacao_anterior_id)
            
            if mudanca.tributacao_nova_id:
                trib_nova = Tributacao.query.get(mudanca.tributacao_nova_id)
            # Buscar tarefas sem responsável da nova tributação
            tarefas_query = db.session.query(RelacionamentoTarefa, Tarefa).join(
                Tarefa, RelacionamentoTarefa.tarefa_id == Tarefa.id
            ).filter(
                RelacionamentoTarefa.empresa_id == empresa.id,
                RelacionamentoTarefa.responsavel_id.is_(None),
                RelacionamentoTarefa.versao_atual == True
            )
            
            # Se for gerente, filtrar apenas tarefas do seu setor
            if usuario.tipo == 'gerente' and usuario.setor_id:
                tarefas_query = tarefas_query.filter(Tarefa.setor_id == usuario.setor_id)
            
            tarefas_sem_responsavel = tarefas_query.all()
            
            # Só adicionar se houver tarefas sem responsável (para gerentes)
            if usuario.tipo == 'admin' or (usuario.tipo == 'gerente' and len(tarefas_sem_responsavel) > 0):
                mudancas_data.append({
                    'mudanca': mudanca,
                    'empresa': empresa,
                    'tributacao_anterior': trib_anterior,
                    'tributacao_nova': trib_nova,
                    'tarefas_sem_responsavel': tarefas_sem_responsavel
                })
        print("esse retornoooooooooooooooooooooooooooooooooooooooooooooo")
        return render_template('gerenciamento_mudancas_tributacao.html',
                             mudancas=mudancas_data,
                             usuario_logado=usuario)
        
    except Exception as e:
        return render_template('gerenciamento_mudancas_tributacao.html', 
                             error=str(e), mudancas=[])


@bp.get('/api/mudancas-tributacao')
def api_mudancas_tributacao():
    """API para buscar mudanças de tributação pendentes"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'message': 'Usuário não autenticado'}), 401
        
        # Verificar se é gerente ou admin
        usuario = Usuario.query.get(user_id)
        if not usuario or usuario.tipo not in ['admin', 'gerente']:
            return jsonify({'success': False, 'message': 'Acesso negado'}), 403
        
        # Filtrar mudanças baseado no tipo de usuário
        if usuario.tipo == 'gerente' and usuario.setor_id:
            # Gerente: apenas mudanças que têm tarefas do seu setor sem responsável
            mudancas_ids = db.session.query(MudancaTributacaoPendente.id).join(
                RelacionamentoTarefa, RelacionamentoTarefa.empresa_id == MudancaTributacaoPendente.empresa_id
            ).join(
                Tarefa, RelacionamentoTarefa.tarefa_id == Tarefa.id
            ).filter(
                MudancaTributacaoPendente.status.in_(['pendente', 'em_revisao']),
                RelacionamentoTarefa.responsavel_id.is_(None),
                RelacionamentoTarefa.versao_atual == True,
                Tarefa.setor_id == usuario.setor_id
            ).distinct()
            
            mudanca_ids_list = [m[0] for m in mudancas_ids.all()]
            mudancas = MudancaTributacaoPendente.query.filter(
                MudancaTributacaoPendente.id.in_(mudanca_ids_list)
            ).order_by(MudancaTributacaoPendente.criado_em.desc()).all() if mudanca_ids_list else []
        else:
            # Admin: todas as mudanças pendentes
            mudancas = MudancaTributacaoPendente.query.filter(
                MudancaTributacaoPendente.status.in_(['pendente', 'em_revisao'])
            ).order_by(MudancaTributacaoPendente.criado_em.desc()).all()
        
        mudancas_data = []
        for mudanca in mudancas:
            mudancas_data.append({
                'id': mudanca.id,
                'empresa_id': mudanca.empresa_id,
                'empresa_nome': mudanca.empresa.nome,
                'tributacao_anterior': mudanca.tributacao_anterior.nome if mudanca.tributacao_anterior else 'N/A',
                'tributacao_nova': mudanca.tributacao_nova.nome,
                'data_mudanca': mudanca.data_mudanca.strftime('%d/%m/%Y'),
                'status': mudanca.status,
                'motivo': mudanca.motivo
            })
        
        return jsonify({
            'success': True,
            'mudancas': mudancas_data,
            'total_pendentes': len(mudancas_data)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'}), 500


@bp.get('/api/mudanca-tributacao/<int:mudanca_id>/tarefas')
def api_tarefas_mudanca_tributacao(mudanca_id):
    """API para buscar tarefas sem responsável de uma mudança de tributação (filtradas por setor do gerente)"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'message': 'Usuário não autenticado'}), 401
        
        # Verificar se é gerente ou admin
        usuario = Usuario.query.get(user_id)
        if not usuario or usuario.tipo not in ['admin', 'gerente']:
            return jsonify({'success': False, 'message': 'Acesso negado'}), 403
        
        mudanca = MudancaTributacaoPendente.query.get(mudanca_id)
        if not mudanca:
            return jsonify({'success': False, 'message': 'Mudança não encontrada'}), 404
        
        # Buscar tarefas sem responsável da empresa
        query = db.session.query(RelacionamentoTarefa, Tarefa).join(
            Tarefa, RelacionamentoTarefa.tarefa_id == Tarefa.id
        ).filter(
            RelacionamentoTarefa.empresa_id == mudanca.empresa_id,
            RelacionamentoTarefa.responsavel_id.is_(None),
            RelacionamentoTarefa.versao_atual == True
        )
        
        # Filtrar por setor se for gerente (não admin)
        if usuario.tipo == 'gerente' and usuario.setor_id:
            query = query.filter(Tarefa.setor_id == usuario.setor_id)
        
        tarefas_sem_responsavel = query.all()
        
        tarefas_data = []
        for rel, tarefa in tarefas_sem_responsavel:
            # Incluir TODAS as tarefas (mensais, trimestrais E anuais)
            # O gerente pode escolher quais vincular e quais deixar em aberto
            tarefas_data.append({
                'relacionamento_id': rel.id,
                'tarefa_id': tarefa.id,
                'nome': tarefa.nome,
                'tipo': tarefa.tipo,
                'descricao': tarefa.descricao,
                'setor': tarefa.setor.nome if tarefa.setor else 'N/A',
                'setor_id': tarefa.setor_id,
                'tarefa_comum': tarefa.tarefa_comum or False
            })
        
        return jsonify({
            'success': True,
            'tarefas': tarefas_data,
            'empresa': {
                'id': mudanca.empresa.id,
                'nome': mudanca.empresa.nome
            },
            'tributacao_nova': {
                'id': mudanca.tributacao_nova.id,
                'nome': mudanca.tributacao_nova.nome
            },
            'tributacao_anterior': {
                'id': mudanca.tributacao_anterior_id,
                'nome': mudanca.tributacao_anterior.nome if mudanca.tributacao_anterior else 'N/A'
            } if mudanca.tributacao_anterior_id else None
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'}), 500


@bp.post('/api/atualizar-responsavel-relacionamentos')
def api_atualizar_responsavel_relacionamentos():
    """API para atualizar responsável de múltiplos relacionamentos (mudanças de tributação)"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'message': 'Usuário não autenticado'}), 401
        
        # Verificar se é gerente ou admin
        usuario = Usuario.query.get(user_id)
        if not usuario or usuario.tipo not in ['admin', 'gerente']:
            return jsonify({'success': False, 'message': 'Acesso negado'}), 403
        
        dados = request.get_json()
        relacionamentos = dados.get('relacionamentos', [])
        mudanca_id = dados.get('mudanca_id')  # Receber mudanca_id se fornecido
        
        print(f"🔵 Recebido: {len(relacionamentos)} relacionamentos, mudanca_id: {mudanca_id}")
        
        if not relacionamentos:
            return jsonify({'success': False, 'message': 'Nenhum relacionamento fornecido'}), 400
        
        atualizados = 0
        empresa_id = None
        erros = []
        
        for item in relacionamentos:
            rel_id = item.get('relacionamento_id')
            responsavel_id = item.get('responsavel_id')
            
            print(f"🔵 Processando: rel_id={rel_id}, responsavel_id={responsavel_id}")
            
            if not rel_id or not responsavel_id:
                erros.append(f"Relacionamento {rel_id} sem dados válidos")
                continue
            
            # Verificar responsável
            responsavel = Usuario.query.get(responsavel_id)
            if not responsavel:
                erros.append(f"Responsável {responsavel_id} não encontrado")
                continue
            
            if not responsavel.ativo:
                erros.append(f"Responsável {responsavel_id} está inativo")
                continue
            
            rel = RelacionamentoTarefa.query.get(rel_id)
            if not rel:
                erros.append(f"Relacionamento {rel_id} não encontrado")
                continue
            
            if not rel.versao_atual:
                erros.append(f"Relacionamento {rel_id} não está na versão atual")
                continue
            
            # Atualizar responsável
            rel.responsavel_id = responsavel_id
            if not empresa_id:
                empresa_id = rel.empresa_id
            atualizados += 1
            print(f"✅ Relacionamento {rel_id} atualizado com responsável {responsavel_id}")
        
        if erros:
            print(f"⚠️ Erros encontrados: {erros}")
        
        # Se forneceu mudanca_id, verificar se todas as tarefas foram processadas
        mudanca_concluida = False
        if mudanca_id and empresa_id:
            mudanca = MudancaTributacaoPendente.query.get(mudanca_id)
            if mudanca:
                # Verificar se ainda há tarefas sem responsável
                tarefas_sem_responsavel = RelacionamentoTarefa.query.filter(
                    RelacionamentoTarefa.empresa_id == empresa_id,
                    RelacionamentoTarefa.responsavel_id.is_(None),
                    RelacionamentoTarefa.versao_atual == True
                ).count()
                
                # Se não há mais tarefas sem responsável, marcar mudança como concluída
                if tarefas_sem_responsavel == 0 and mudanca.status in ['pendente', 'em_revisao']:
                    mudanca.status = 'concluida'
                    mudanca.revisado_por = user_id
                    mudanca.data_revisao = datetime.now()
                    mudanca_concluida = True
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'✅ {atualizados} tarefa(s) vinculada(s) com sucesso!',
            'atualizados': atualizados,
            'mudanca_concluida': mudanca_concluida
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'}), 500


@bp.post('/api/desativar-tarefas')
def api_desativar_tarefas():
    """API para desativar tarefas (marcar como não vinculadas)"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'message': 'Usuário não autenticado'}), 401
        
        # Verificar se é gerente ou admin
        usuario = Usuario.query.get(user_id)
        if not usuario or usuario.tipo not in ['admin', 'gerente']:
            return jsonify({'success': False, 'message': 'Acesso negado'}), 403
        
        dados = request.get_json()
        relacionamentos_ids = dados.get('relacionamentos_ids', [])
        mudanca_id = dados.get('mudanca_id')  # Receber mudanca_id se fornecido
        
        if not relacionamentos_ids:
            return jsonify({'success': False, 'message': 'Nenhum relacionamento fornecido'}), 400
        
        desativados = 0
        empresa_id = None
        
        for rel_id in relacionamentos_ids:
            rel = RelacionamentoTarefa.query.get(rel_id)
            if rel and rel.versao_atual:
                # Desativar a tarefa (não será mais exibida como pendente)
                rel.versao_atual = False
                if not empresa_id:
                    empresa_id = rel.empresa_id
                desativados += 1
        
        # Se forneceu mudanca_id, verificar se todas as tarefas foram processadas
        mudanca_concluida = False
        if mudanca_id and empresa_id:
            mudanca = MudancaTributacaoPendente.query.get(mudanca_id)
            if mudanca:
                # Verificar se ainda há tarefas sem responsável
                tarefas_sem_responsavel = RelacionamentoTarefa.query.filter(
                    RelacionamentoTarefa.empresa_id == empresa_id,
                    RelacionamentoTarefa.responsavel_id.is_(None),
                    RelacionamentoTarefa.versao_atual == True
                ).count()
                
                # Se não há mais tarefas sem responsável, marcar mudança como concluída
                if tarefas_sem_responsavel == 0 and mudanca.status in ['pendente', 'em_revisao']:
                    mudanca.status = 'concluida'
                    mudanca.revisado_por = user_id
                    mudanca.data_revisao = datetime.now()
                    mudanca_concluida = True
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'✅ {desativados} tarefa(s) marcada(s) como "Não vincular"',
            'desativados': desativados,
            'mudanca_concluida': mudanca_concluida
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'}), 500


@bp.post('/api/vincular-responsavel-mudanca')
def api_vincular_responsavel_mudanca():
    """API para vincular responsável às tarefas de uma mudança de tributação"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'message': 'Usuário não autenticado'}), 401
        
        # Verificar se é gerente ou admin
        usuario = Usuario.query.get(user_id)
        if not usuario or usuario.tipo not in ['admin', 'gerente']:
            return jsonify({'success': False, 'message': 'Acesso negado'}), 403
        
        data = request.get_json()
        mudanca_id = data.get('mudanca_id')
        responsavel_id = data.get('responsavel_id')
        tarefas = data.get('tarefas', [])
        
        if not mudanca_id or not responsavel_id or not tarefas:
            return jsonify({'success': False, 'message': 'Dados obrigatórios não fornecidos'}), 400
        
        mudanca = MudancaTributacaoPendente.query.get(mudanca_id)
        if not mudanca:
            return jsonify({'success': False, 'message': 'Mudança não encontrada'}), 404
        
        # Verificar se responsável existe
        responsavel = Usuario.query.get(responsavel_id)
        if not responsavel:
            return jsonify({'success': False, 'message': 'Responsável não encontrado'}), 404
        
        vinculacoes_criadas = 0
        
        for tarefa_data in tarefas:
            relacionamento_id = tarefa_data.get('relacionamento_id')
            if not relacionamento_id:
                continue
            
            # Buscar relacionamento
            rel = RelacionamentoTarefa.query.get(relacionamento_id)
            if not rel:
                continue
            
            # Vincular responsável
            rel.responsavel_id = responsavel_id
            vinculacoes_criadas += 1
        
        # Marcar mudança como em revisão se ainda estiver pendente
        if mudanca.status == 'pendente':
            mudanca.status = 'em_revisao'
            mudanca.revisado_por = user_id
            mudanca.data_revisao = datetime.now()
        
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': f'{vinculacoes_criadas} tarefa(s) vinculada(s) com sucesso!'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'}), 500


@bp.post('/api/verificar-concluir-mudanca')
def api_verificar_concluir_mudanca():
    """API para verificar e concluir mudança de tributação se todas as tarefas foram processadas"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'message': 'Usuário não autenticado'}), 401
        
        # Verificar se é gerente ou admin
        usuario = Usuario.query.get(user_id)
        if not usuario or usuario.tipo not in ['admin', 'gerente']:
            return jsonify({'success': False, 'message': 'Acesso negado'}), 403
        
        data = request.get_json()
        mudanca_id = data.get('mudanca_id')
        
        if not mudanca_id:
            return jsonify({'success': False, 'message': 'ID da mudança não fornecido'}), 400
        
        mudanca = MudancaTributacaoPendente.query.get(mudanca_id)
        if not mudanca:
            return jsonify({'success': False, 'message': 'Mudança não encontrada'}), 404
        
        # Verificar se ainda há tarefas sem responsável
        tarefas_sem_responsavel = RelacionamentoTarefa.query.filter(
            RelacionamentoTarefa.empresa_id == mudanca.empresa_id,
            RelacionamentoTarefa.responsavel_id.is_(None),
            RelacionamentoTarefa.versao_atual == True
        ).count()
        
        # Se não há mais tarefas sem responsável e mudança ainda está pendente, marcar como concluída
        if tarefas_sem_responsavel == 0 and mudanca.status in ['pendente', 'em_revisao']:
            mudanca.status = 'concluida'
            mudanca.revisado_por = user_id
            mudanca.data_revisao = datetime.now()
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Mudança de tributação concluída automaticamente!',
                'mudanca_concluida': True
            })
        else:
            return jsonify({
                'success': True,
                'message': f'Ainda há {tarefas_sem_responsavel} tarefa(s) sem responsável.',
                'mudanca_concluida': False,
                'tarefas_sem_responsavel': tarefas_sem_responsavel
            })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'}), 500


@bp.post('/api/concluir-mudanca-tributacao')
def api_concluir_mudanca_tributacao():
    """API para concluir uma mudança de tributação"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'message': 'Usuário não autenticado'}), 401
        
        # Verificar se é gerente ou admin
        usuario = Usuario.query.get(user_id)
        if not usuario or usuario.tipo not in ['admin', 'gerente']:
            return jsonify({'success': False, 'message': 'Acesso negado'}), 403
        
        data = request.get_json()
        mudanca_id = data.get('mudanca_id')
        observacoes = data.get('observacoes', '')
        
        if not mudanca_id:
            return jsonify({'success': False, 'message': 'ID da mudança não fornecido'}), 400
        
        mudanca = MudancaTributacaoPendente.query.get(mudanca_id)
        if not mudanca:
            return jsonify({'success': False, 'message': 'Mudança não encontrada'}), 404
        
        # Verificar se todas as tarefas têm responsável
        tarefas_sem_responsavel = RelacionamentoTarefa.query.filter(
            RelacionamentoTarefa.empresa_id == mudanca.empresa_id,
            RelacionamentoTarefa.responsavel_id.is_(None),
            RelacionamentoTarefa.versao_atual == True
        ).count()
        
        if tarefas_sem_responsavel > 0:
            return jsonify({
                'success': False, 
                'message': f'Ainda existem {tarefas_sem_responsavel} tarefa(s) sem responsável. Todas as tarefas devem ter responsáveis antes de concluir a mudança.'
            }), 400
        
        # Marcar mudança como concluída
        mudanca.status = 'concluida'
        mudanca.revisado_por = user_id
        mudanca.data_revisao = datetime.now()
        mudanca.observacoes_revisao = observacoes
        
        # Criar registro no histórico
        historico = HistoricoMudancaTributacao(
            empresa_id=mudanca.empresa_id,
            tributacao_anterior_id=mudanca.tributacao_anterior_id,
            tributacao_nova_id=mudanca.tributacao_nova_id,
            data_mudanca=mudanca.data_mudanca,
            motivo=mudanca.motivo,
            criado_por=mudanca.criado_por
        )
        db.session.add(historico)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Mudança de tributação concluída com sucesso!'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'}), 500


# ===== GESTÃO DE TAREFAS ANUAIS =====

@bp.get('/tarefas-anuais')
def painel_tarefas_anuais():
    """Painel específico para gerenciar tarefas anuais"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return redirect(url_for('auth.login_page'))
        
        usuario = Usuario.query.get(user_id)
        if not usuario or usuario.tipo not in ['admin', 'gerente']:
            return redirect(url_for('auth.login_page'))
        
        print(f"✅ [Tarefas Anuais] Renderizando painel para {usuario.nome}")
        return render_template('gerenciamento_tarefas_anuais.html', usuario=usuario)
        
    except Exception as e:
        print(f"❌ [Tarefas Anuais] Erro: {str(e)}")
        return redirect(url_for('gerenciamento.gerenciamento_page'))


@bp.get('/api/tarefas-anuais-disponiveis')
def api_tarefas_anuais_disponiveis():
    """API para buscar tarefas anuais disponíveis para vinculação"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'message': 'Usuário não autenticado'}), 401
        
        usuario = Usuario.query.get(user_id)
        if not usuario or usuario.tipo not in ['admin', 'gerente']:
            return jsonify({'success': False, 'message': 'Acesso negado'}), 403
        
        # Buscar tarefas anuais
        query = Tarefa.query.filter(Tarefa.tipo == 'Anual')
        
        # Filtrar por setor se for gerente
        if usuario.tipo == 'gerente' and usuario.setor_id:
            query = query.filter(Tarefa.setor_id == usuario.setor_id)
        
        tarefas = query.order_by(Tarefa.nome).all()
        
        tarefas_data = [{
            'id': t.id,
            'nome': t.nome,
            'descricao': t.descricao,
            'setor': t.setor.nome if t.setor else 'N/A',
            'tributacao': t.tributacao.nome if t.tributacao else 'Comum',
            'tarefa_comum': t.tarefa_comum
        } for t in tarefas]
        
        return jsonify({'success': True, 'tarefas': tarefas_data})
        
    except Exception as e:
        import traceback
        print(f"❌ [Tarefas Anuais] Erro: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'}), 500


@bp.post('/api/vincular-tarefa-anual')
def api_vincular_tarefa_anual():
    """API para vincular uma tarefa anual a um usuário e empresas"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'message': 'Usuário não autenticado'}), 401
        
        usuario = Usuario.query.get(user_id)
        if not usuario or usuario.tipo not in ['admin', 'gerente']:
            return jsonify({'success': False, 'message': 'Acesso negado'}), 403
        
        data = request.get_json()
        tarefa_id = data.get('tarefa_id')
        funcionario_id = data.get('funcionario_id')
        empresas_ids = data.get('empresas_ids', [])
        ano = data.get('ano')  # Ano de execução (ex: 2025)
        
        if not tarefa_id or not funcionario_id or not empresas_ids or not ano:
            return jsonify({'success': False, 'message': 'Dados incompletos'}), 400
        
        # Verificar tarefa
        tarefa = Tarefa.query.get(tarefa_id)
        if not tarefa or tarefa.tipo != 'Anual':
            return jsonify({'success': False, 'message': 'Tarefa anual não encontrada'}), 404
        
        # Verificar funcionário
        funcionario = Usuario.query.get(funcionario_id)
        if not funcionario or not funcionario.ativo:
            return jsonify({'success': False, 'message': 'Funcionário não encontrado'}), 404
        
        # Verificar setor do gerente
        if usuario.tipo == 'gerente' and usuario.setor_id:
            if funcionario.setor_id != usuario.setor_id:
                return jsonify({'success': False, 'message': 'Funcionário não pertence ao seu setor'}), 403
            if tarefa.setor_id != usuario.setor_id:
                return jsonify({'success': False, 'message': 'Tarefa não pertence ao seu setor'}), 403
        
        criados = 0
        duplicados = 0
        erros = []
        
        for empresa_id in empresas_ids:
            try:
                empresa = Empresa.query.get(empresa_id)
                if not empresa or not empresa.ativo:
                    erros.append(f'Empresa ID {empresa_id} não encontrada ou inativa')
                    continue
                
                # Verificar compatibilidade de tributação
                if not tarefa.tarefa_comum:
                    if tarefa.tributacao_id and empresa.tributacao_id != tarefa.tributacao_id:
                        erros.append(f'{empresa.nome}: tributação incompatível')
                        continue
                
                # Verificar se já existe vinculação ativa para esta tarefa+empresa no ano
                vinculacao_existente = RelacionamentoTarefa.query.filter_by(
                    empresa_id=empresa_id,
                    tarefa_id=tarefa_id,
                    versao_atual=True,
                    status='ativa'
                ).filter(
                    RelacionamentoTarefa.periodo.like(f'{ano}%')
                ).first()
                
                if vinculacao_existente:
                    duplicados += 1
                    continue
                
                # Criar vinculação para o ano todo (usar período como YYYY)
                novo_rel = RelacionamentoTarefa(
                    empresa_id=empresa_id,
                    tarefa_id=tarefa_id,
                    responsavel_id=funcionario_id,
                    periodo=str(ano),  # Armazenar só o ano
                    versao_atual=True,
                    status='ativa',
                    data_inicio=date(ano, 1, 1),
                    data_fim=date(ano, 12, 31)
                )
                
                db.session.add(novo_rel)
                criados += 1
                print(f"✅ [Tarefa Anual] Criada: {empresa.nome} → {tarefa.nome} → {funcionario.nome} (Ano: {ano})")
                
            except Exception as e:
                erros.append(f'Empresa ID {empresa_id}: {str(e)}')
                continue
        
        # Commit
        try:
            db.session.commit()
            print(f"✅ [Tarefas Anuais] Commit realizado: {criados} vinculações criadas")
        except Exception as e:
            db.session.rollback()
            print(f"❌ [Tarefas Anuais] Erro no commit: {str(e)}")
            return jsonify({'success': False, 'message': f'Erro ao salvar: {str(e)}'}), 500
        
        # Mensagem final
        mensagens = []
        if criados > 0:
            mensagens.append(f'{criados} vinculação(ões) criada(s)')
        if duplicados > 0:
            mensagens.append(f'{duplicados} já vinculada(s)')
        
        mensagem_final = ', '.join(mensagens) if mensagens else 'Nenhuma vinculação realizada'
        
        if erros:
            mensagem_final += f'\n\nAvisos:\n' + '\n'.join(erros[:5])
        
        return jsonify({
            'success': True,
            'message': mensagem_final,
            'criados': criados,
            'duplicados': duplicados,
            'erros': erros[:5]
        })
        
    except Exception as e:
        db.session.rollback()
        import traceback
        print(f"❌ [Tarefas Anuais] Erro: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'}), 500