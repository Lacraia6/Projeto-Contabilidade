from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, current_app
from app.db import db
from app.models import Empresa, RelacionamentoTarefa, Periodo, Tarefa, Usuario, Retificacao
from app.utils import (
    get_previous_period, get_previous_period_label, convert_period_to_label, 
    validate_period_format, should_show_task_by_type
)
from sqlalchemy.orm import joinedload
from datetime import datetime
import re
from app.utils import get_current_period_label, gerar_periodo_label
from app.services.tarefa_service import TarefaService
from app.services.empresa_service import EmpresaService
from app.blueprints.api_v1 import invalidate_tarefas_cache, invalidate_empresas_cache

bp = Blueprint('dashboard', __name__, url_prefix='')


# Funções consolidadas em app/utils.py


def _build_periodos(empresa_id, periodo_label, user_id, tarefa_id):
    """Constrói lista de períodos com filtros aplicados - OTIMIZADA com joinedload"""
    # Usar joinedload para evitar N+1 queries
    query = db.session.query(Periodo).join(RelacionamentoTarefa).join(Tarefa).join(Empresa)
    
    if periodo_label:
        query = query.filter(Periodo.periodo_label == periodo_label)
    if empresa_id:
        query = query.filter(RelacionamentoTarefa.empresa_id == empresa_id)
    if user_id:
        query = query.filter(RelacionamentoTarefa.responsavel_id == user_id)
    if tarefa_id:
        query = query.filter(RelacionamentoTarefa.tarefa_id == tarefa_id)
    
    # Carregar relacionamentos de uma vez
    periodos = query.options(
        joinedload(Periodo.relacionamento_tarefa).joinedload(RelacionamentoTarefa.tarefa),
        joinedload(Periodo.relacionamento_tarefa).joinedload(RelacionamentoTarefa.empresa)
    ).all()
    
    itens = []
    for p in periodos:
        rel = p.relacionamento_tarefa
        tar = rel.tarefa
        emp = rel.empresa
        
        itens.append({
            "periodo_id": p.id,
            "nome": tar.nome,  # Nome da tarefa
            "tarefa_nome": tar.nome,  # Alias para compatibilidade
            "tipo": tar.tipo,
            "status": p.status or 'pendente',
            "vencimento": p.fim.strftime('%d/%m/%Y') if p.fim else None,
            "empresa_ativa": bool(getattr(emp, 'ativo', True)),
            "empresa_nome": emp.nome,
            "data_conclusao": p.data_conclusao.strftime('%d/%m/%Y') if p.data_conclusao else None,
            "data_retificacao": p.data_retificacao.strftime('%d/%m/%Y') if p.data_retificacao else None,
            "contador_retificacoes": p.contador_retificacoes or 0,
            "periodo_label": p.periodo_label
        })
    return itens




def _build_periodos_multiplas(empresa_filter, periodo_label, user_id, tarefa_filter):
    """Constrói lista de períodos com suporte a múltiplas empresas e tarefas - OTIMIZADA com joinedload"""
    # Determinar se é período atual ou futuro
    periodo_atual = get_previous_period_label()  # Período anterior (padrão)
    is_periodo_atual = periodo_label == periodo_atual
    
    # Usar joinedload para evitar N+1 queries
    query = db.session.query(Periodo).join(RelacionamentoTarefa).join(Tarefa).join(Empresa)
    
    # Filtrar por empresas (suporte a múltiplas)
    if empresa_filter:
        if isinstance(empresa_filter, list):
            query = query.filter(RelacionamentoTarefa.empresa_id.in_(empresa_filter))
        else:
            query = query.filter(RelacionamentoTarefa.empresa_id == empresa_filter)
    
    if user_id:
        query = query.filter(RelacionamentoTarefa.responsavel_id == user_id)
    
    # Filtrar por tarefas (suporte a múltiplas)
    if tarefa_filter:
        if isinstance(tarefa_filter, list):
            query = query.filter(RelacionamentoTarefa.tarefa_id.in_(tarefa_filter))
        else:
            query = query.filter(RelacionamentoTarefa.tarefa_id == tarefa_filter)
    
    # NOVA LÓGICA: Para período atual, mostrar todas as tarefas (ativas e antigas)
    # Para períodos futuros, mostrar apenas tarefas ativas
    if not is_periodo_atual:
        # Para períodos futuros, mostrar apenas tarefas ativas (versao_atual = True)
        query = query.filter(RelacionamentoTarefa.versao_atual == True)
    
    # Carregar relacionamentos de uma vez
    periodos = query.options(
        joinedload(Periodo.relacionamento_tarefa).joinedload(RelacionamentoTarefa.tarefa),
        joinedload(Periodo.relacionamento_tarefa).joinedload(RelacionamentoTarefa.empresa)
    ).all()
    
    itens = []
    for p in periodos:
        rel = p.relacionamento_tarefa
        tar = rel.tarefa
        emp = rel.empresa
        
        # Excluir tarefas anuais (são tratadas separadamente)
        if tar.tipo == 'Anual':
            continue
        
        # Para tarefas trimestrais, não filtrar por período_label diretamente
        # A filtragem será feita pela lógica de tipo de tarefa
        if tar.tipo == 'Trimestral':
            # Aplicar filtragem inteligente por tipo de tarefa
            if not should_show_task_by_type(tar.tipo, periodo_label, p.periodo_label):
                continue
        else:
            # Para tarefas mensais, aplicar filtro de período normalmente
            if periodo_label and p.periodo_label != periodo_label:
                continue
        
        # Determinar se é tarefa antiga (desativada)
        is_tarefa_antiga = not rel.versao_atual
        
        itens.append({
            "periodo_id": p.id,
            "nome": tar.nome,  # Nome da tarefa
            "tarefa_nome": tar.nome,  # Alias para compatibilidade
            "tipo": tar.tipo,
            "status": p.status or 'pendente',
            "vencimento": p.fim.strftime('%d/%m/%Y') if p.fim else None,
            "empresa_ativa": bool(getattr(emp, 'ativo', True)),
            "empresa_nome": emp.nome,
            "data_conclusao": p.data_conclusao.strftime('%d/%m/%Y') if p.data_conclusao else None,
            "data_retificacao": p.data_retificacao.strftime('%d/%m/%Y') if p.data_retificacao else None,
            "contador_retificacoes": p.contador_retificacoes or 0,
            "periodo_label": p.periodo_label,
            "is_tarefa_antiga": is_tarefa_antiga,  # Nova propriedade
            "motivo_desativacao": rel.motivo_desativacao if is_tarefa_antiga else None
        })
    return itens


@bp.get('/')
@bp.get('/dashboard')
def return_dashboard():
    """Página principal do dashboard do funcionário"""
    try:
        periodo_input = request.args.get('periodo', get_previous_period())
        empresa_id = request.args.get('empresa_id', type=int)
        empresa_ids = request.args.get('empresa_ids', '')
        tarefa_id = request.args.get('tarefa_id', type=int)
        tarefa_ids = request.args.get('tarefa_ids', '')
        user_id = session.get('user_id')
        
        # Processar múltiplas empresas
        empresa_ids_list = []
        if empresa_ids:
            try:
                empresa_ids_list = [int(id.strip()) for id in empresa_ids.split(',') if id.strip().isdigit()]
            except ValueError:
                empresa_ids_list = []
        
        # Processar múltiplas tarefas
        tarefa_ids_list = []
        if tarefa_ids:
            try:
                tarefa_ids_list = [int(id.strip()) for id in tarefa_ids.split(',') if id.strip().isdigit()]
            except ValueError:
                tarefa_ids_list = []
        
        # Validar período
        if not validate_period_format(periodo_input):
            periodo_input = '08/2025'  # Valor padrão
        
        periodo_atual = convert_period_to_label(periodo_input)
        
        # Buscar dados do usuário para filtrar por setor
        usuario = Usuario.query.get(user_id) if user_id else None
        user_tipo = usuario.tipo if usuario else 'normal'
        user_setor_id = usuario.setor_id if usuario else None
        
        # Buscar empresas que têm tarefas relacionadas ao usuário
        empresas_query = db.session.query(Empresa).join(
            RelacionamentoTarefa, Empresa.id == RelacionamentoTarefa.empresa_id
        ).filter(RelacionamentoTarefa.responsavel_id == user_id).distinct().order_by(Empresa.nome)
        
        # Aplicar filtro de setor apenas para gerentes
        if user_tipo == 'gerente' and user_setor_id:
            empresas_query = empresas_query.filter(Tarefa.setor_id == user_setor_id)
        
        empresas = empresas_query.all()
        
        # Buscar tarefas relacionadas ao usuário
        tarefas_usuario = db.session.query(Tarefa).join(
            RelacionamentoTarefa, Tarefa.id == RelacionamentoTarefa.tarefa_id
        ).filter(RelacionamentoTarefa.responsavel_id == user_id)
        
        # Aplicar filtro de setor apenas para gerentes
        if user_tipo == 'gerente' and user_setor_id:
            tarefas_usuario = tarefas_usuario.filter(Tarefa.setor_id == user_setor_id)
        
        if empresa_id:
            tarefas_usuario = tarefas_usuario.filter(RelacionamentoTarefa.empresa_id == empresa_id)
        
        tarefas_usuario = tarefas_usuario.distinct().order_by(Tarefa.nome).all()

        # Buscar tarefas do período
        # Usar empresa_id se fornecido, senão usar empresa_ids_list
        empresa_filter = empresa_id if empresa_id else (empresa_ids_list if empresa_ids_list else None)
        # Usar tarefa_id se fornecido, senão usar tarefa_ids_list
        tarefa_filter = tarefa_id if tarefa_id else (tarefa_ids_list if tarefa_ids_list else None)
        tarefas = _build_periodos_multiplas(empresa_filter, periodo_atual, user_id, tarefa_filter)
        
        # Calcular resumo
        resumo = {"pendentes": 0, "fazendo": 0, "concluidas": 0}
        for t in tarefas:
            if t['status'] == 'pendente':
                resumo['pendentes'] += 1
            elif t['status'] == 'fazendo':
                resumo['fazendo'] += 1
            elif t['status'] in ['concluida', 'retificada']:
                resumo['concluidas'] += 1
        
        # Calcular taxa de conclusão
        total_tarefas = len(tarefas)
        taxa_conclusao = (resumo['concluidas'] / total_tarefas * 100) if total_tarefas > 0 else 0
        
        return render_template('dashboard.html',
            periodo_atual=periodo_input,
            empresa_atual=empresa_id,
            tarefa_atual=tarefa_id,
            empresas=empresas,
            tarefas=tarefas_usuario,
            tarefas_list=tarefas,
            resumo=resumo,
            taxa_conclusao=taxa_conclusao,
            total_tarefas=total_tarefas,
            user_setor_nome=usuario.setor.nome if usuario and usuario.setor else 'Todos os Setores',
        )
        
    except Exception as e:
        print(f"Erro no dashboard: {e}")
        return render_template('dashboard.html',
            periodo_atual='08/2025',
            empresa_atual=None,
            tarefa_atual=None,
            empresas=[],
            tarefas=[],
            tarefas_list=[],
            resumo={"pendentes": 0, "fazendo": 0, "concluidas": 0},
            taxa_conclusao=0,
            total_tarefas=0,
            user_setor_nome='Todos os Setores',
        )


@bp.get('/api/dashboard/empresas')
def get_empresas_dashboard():
    """API para buscar empresas do dashboard"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'message': 'Usuário não autenticado'}), 401
        
        # Buscar dados do usuário
        usuario = Usuario.query.get(user_id)
        user_tipo = usuario.tipo if usuario else 'normal'
        user_setor_id = usuario.setor_id if usuario else None
        
        # Buscar empresas que têm tarefas relacionadas ao usuário - OTIMIZADA
        empresas_query = db.session.query(Empresa).join(
            RelacionamentoTarefa, Empresa.id == RelacionamentoTarefa.empresa_id
        ).filter(RelacionamentoTarefa.responsavel_id == user_id).distinct()
        
        # Aplicar filtro de setor apenas para gerentes
        if user_tipo == 'gerente' and user_setor_id:
            empresas_query = empresas_query.join(Tarefa, RelacionamentoTarefa.tarefa_id == Tarefa.id)
            empresas_query = empresas_query.filter(Tarefa.setor_id == user_setor_id)
        
        empresas = empresas_query.order_by(Empresa.nome).all()
        
        empresas_json = []
        for empresa in empresas:
            empresas_json.append({
                'id': empresa.id,
                'nome': empresa.nome,
                'codigo': empresa.codigo,
                'ativo': empresa.ativo
            })
        
        return jsonify({'success': True, 'empresas': empresas_json})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro ao buscar empresas: {str(e)}'}), 500


@bp.get('/api/dashboard/tarefas')
def get_tarefas_dashboard():
    """API para buscar tarefas do dashboard"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'message': 'Usuário não autenticado'}), 401
        
        # Buscar dados do usuário
        usuario = Usuario.query.get(user_id)
        user_tipo = usuario.tipo if usuario else 'normal'
        user_setor_id = usuario.setor_id if usuario else None
        
        # Buscar tarefas relacionadas ao usuário - OTIMIZADA
        tarefas_query = db.session.query(Tarefa).join(
            RelacionamentoTarefa, Tarefa.id == RelacionamentoTarefa.tarefa_id
        ).filter(RelacionamentoTarefa.responsavel_id == user_id)
        
        # Aplicar filtro de setor apenas para gerentes
        if user_tipo == 'gerente' and user_setor_id:
            tarefas_query = tarefas_query.filter(Tarefa.setor_id == user_setor_id)
        
        tarefas = tarefas_query.distinct().order_by(Tarefa.nome).all()
        
        tarefas_json = []
        for tarefa in tarefas:
            tarefas_json.append({
                'id': tarefa.id,
                'nome': tarefa.nome,
                'tipo': tarefa.tipo,
                'setor_id': tarefa.setor_id
            })
        
        return jsonify({'success': True, 'tarefas': tarefas_json})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro ao buscar tarefas: {str(e)}'}), 500


@bp.get('/api/dashboard/tarefas-anuais')
def get_tarefas_anuais():
    """API para buscar tarefas anuais do dashboard"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'message': 'Usuário não autenticado'}), 401
        
        # Buscar dados do usuário
        usuario = Usuario.query.get(user_id)
        user_tipo = usuario.tipo if usuario else 'normal'
        user_setor_id = usuario.setor_id if usuario else None
        
        # Buscar tarefas anuais relacionadas ao usuário
        query = db.session.query(Periodo, RelacionamentoTarefa, Tarefa, Empresa).join(
            RelacionamentoTarefa, Periodo.relacionamento_tarefa_id == RelacionamentoTarefa.id
        ).join(
            Tarefa, RelacionamentoTarefa.tarefa_id == Tarefa.id
        ).join(
            Empresa, RelacionamentoTarefa.empresa_id == Empresa.id
        ).filter(
            Tarefa.tipo == 'Anual',
            RelacionamentoTarefa.responsavel_id == user_id
        )
        
        # Aplicar filtro de setor apenas para gerentes
        if user_tipo == 'gerente' and user_setor_id:
            query = query.filter(Tarefa.setor_id == user_setor_id)
        
        tarefas_anuais = []
        for p, rel, tar, emp in query.all():
            tarefas_anuais.append({
                "periodo_id": p.id,
                "nome": tar.nome,
                "tipo": tar.tipo,
                "status": p.status or 'pendente',
                "vencimento": p.fim.strftime('%d/%m/%Y') if p.fim else None,
                "empresa_nome": emp.nome,
                "data_conclusao": p.data_conclusao.strftime('%d/%m/%Y') if p.data_conclusao else None,
                "data_retificacao": p.data_retificacao.strftime('%d/%m/%Y') if p.data_retificacao else None,
                "contador_retificacoes": p.contador_retificacoes or 0,
                "periodo_label": p.periodo_label
            })
        
        return jsonify({'success': True, 'tarefas_anuais': tarefas_anuais})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro ao buscar tarefas anuais: {str(e)}'}), 500


@bp.get('/api/dashboard/resumo')
def api_resumo():
    """API para buscar resumo de tarefas do dashboard"""
    try:
        periodo_input = request.args.get('periodo', '08/2025')
        empresa_id = request.args.get('empresa_id', type=int)
        empresa_ids = request.args.get('empresa_ids', '')
        tarefa_id = request.args.get('tarefa_id', type=int)
        tarefa_ids = request.args.get('tarefa_ids', '')
        user_id = session.get('user_id')
        
        # Processar múltiplas empresas
        empresa_ids_list = []
        if empresa_ids:
            try:
                empresa_ids_list = [int(id.strip()) for id in empresa_ids.split(',') if id.strip().isdigit()]
            except ValueError:
                empresa_ids_list = []
        
        # Processar múltiplas tarefas
        tarefa_ids_list = []
        if tarefa_ids:
            try:
                tarefa_ids_list = [int(id.strip()) for id in tarefa_ids.split(',') if id.strip().isdigit()]
            except ValueError:
                tarefa_ids_list = []
        
        # Validar período
        if not validate_period_format(periodo_input):
            return jsonify({
                'success': False,
                'message': 'Formato de período inválido. Use MM/AAAA'
            }), 400
        
        periodo_atual = convert_period_to_label(periodo_input)
        
        # Buscar tarefas
        empresa_filter = empresa_id if empresa_id else (empresa_ids_list if empresa_ids_list else None)
        tarefa_filter = tarefa_id if tarefa_id else (tarefa_ids_list if tarefa_ids_list else None)
        tarefas = _build_periodos_multiplas(empresa_filter, periodo_atual, user_id, tarefa_filter)
        
        # Calcular resumo
        resumo = {"pendentes": 0, "fazendo": 0, "concluidas": 0}
        for t in tarefas:
            if t['status'] == 'pendente':
                resumo['pendentes'] += 1
            elif t['status'] == 'fazendo':
                resumo['fazendo'] += 1
            elif t['status'] in ['concluida', 'retificada']:
                resumo['concluidas'] += 1
        
        # Calcular taxa de conclusão
        total_tarefas = len(tarefas)
        taxa_conclusao = (resumo['concluidas'] / total_tarefas * 100) if total_tarefas > 0 else 0
        
        # Preparar dados das tarefas para JSON
        tarefas_json = []
        for t in tarefas:
            tarefas_json.append({
                'periodo_id': t['periodo_id'],
                'nome': t['nome'],
                'tipo': t['tipo'],
                'status': t['status'],
                'vencimento': t['vencimento'],
                'empresa_nome': t['empresa_nome'],
                'data_conclusao': t['data_conclusao'],
                'data_retificacao': t['data_retificacao'],
                'contador_retificacoes': t['contador_retificacoes'],
                'periodo_label': t['periodo_label']
            })
        
        return jsonify({
            'success': True,
            'resumo': resumo,
            'tarefas': tarefas_json,
            'total_encontradas': len(tarefas),
            'taxa_conclusao': taxa_conclusao
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro ao buscar resumo: {str(e)}'
        }), 500


@bp.post('/api/dashboard/concluir-tarefa')
def concluir_tarefa():
    """API para concluir uma tarefa"""
    try:
        data = request.get_json()
        periodo_id = data.get('periodo_id')
        
        if not periodo_id:
            return jsonify({'success': False, 'message': 'ID do período é obrigatório'}), 400
        
        # Buscar o período
        periodo = Periodo.query.get(periodo_id)
        if not periodo:
            return jsonify({'success': False, 'message': 'Período não encontrado'}), 404
        
        # Atualizar status
        periodo.status = 'concluida'
        periodo.data_conclusao = datetime.now()
        periodo.atualizado_em = datetime.now()
        
        db.session.commit()
        
        # Invalidar cache relacionado
        invalidate_tarefas_cache()
        invalidate_empresas_cache()
        
        return jsonify({'success': True, 'message': 'Tarefa concluída com sucesso!'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Erro ao concluir tarefa: {str(e)}'}), 500


@bp.post('/api/dashboard/retificar-tarefa')
def retificar_tarefa():
    """API para retificar uma tarefa"""
    try:
        data = request.get_json()
        periodo_id = data.get('periodo_id')
        motivo = data.get('motivo', '')
        
        if not periodo_id:
            return jsonify({'success': False, 'message': 'ID do período é obrigatório'}), 400
        
        # Buscar o período
        periodo = Periodo.query.get(periodo_id)
        if not periodo:
            return jsonify({'success': False, 'message': 'Período não encontrado'}), 404
        
        # Atualizar status e contador
        periodo.status = 'retificada'
        periodo.data_retificacao = datetime.now()
        periodo.contador_retificacoes = (periodo.contador_retificacoes or 0) + 1
        periodo.atualizado_em = datetime.now()
        
        # Criar registro de retificação
        retificacao = Retificacao(
            periodo_id=periodo_id,
            usuario_id=session.get('user_id'),
            motivo=motivo,
            criado_em=datetime.now()
        )
        db.session.add(retificacao)
        
        db.session.commit()
        
        # Invalidar cache relacionado
        invalidate_tarefas_cache()
        invalidate_empresas_cache()
        
        return jsonify({'success': True, 'message': 'Tarefa retificada com sucesso!'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Erro ao retificar tarefa: {str(e)}'}), 500
