#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Blueprint para o Sistema Completo de Tarefas
Implementa a lógica completa: Empresa + Tributação + Tarefa + Responsável + Período
"""

from flask import Blueprint, render_template, request, session, jsonify, redirect, url_for
from app.db import db
from app.models import (
    Empresa, Tributacao, Usuario, Tarefa, Setor, VinculacaoEmpresaTributacao,
    PeriodoExecucao, AtribuicaoTarefa, ExecucaoTarefa, ResponsavelPadraoTarefa,
    HistoricoMudancaTributacao, ChecklistEmpresa
)
from datetime import datetime, date, timedelta
import json

bp = Blueprint('sistema_completo_tarefas', __name__, url_prefix='/sistema-completo-tarefas')


@bp.get('/')
def dashboard():
    """Dashboard principal do sistema completo de tarefas"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return redirect(url_for('auth.login_page'))
        
        # Verificar tipo de usuário
        usuario = Usuario.query.get(user_id)
        if not usuario:
            return redirect(url_for('auth.login'))
        
        # Buscar dados baseados no tipo de usuário
        if usuario.tipo == 'admin':
            empresas = Empresa.query.filter_by(ativo=True).order_by(Empresa.nome).all()
            atribuicoes = AtribuicaoTarefa.query.filter_by(status='pendente').all()
        elif usuario.tipo == 'gerente':
            empresas = Empresa.query.filter_by(ativo=True).order_by(Empresa.nome).all()
            atribuicoes = AtribuicaoTarefa.query.join(Usuario).filter(
                Usuario.setor_id == usuario.setor_id,
                AtribuicaoTarefa.status == 'pendente'
            ).all()
        elif usuario.tipo == 'supervisor':
            empresas = Empresa.query.filter_by(ativo=True).order_by(Empresa.nome).all()
            atribuicoes = []
        else:  # normal (funcionário)
            empresas = []
            atribuicoes = AtribuicaoTarefa.query.filter_by(
                responsavel_id=user_id,
                status='pendente'
            ).all()
        
        # Buscar períodos ativos
        periodos = PeriodoExecucao.query.filter_by(status='ativo').order_by(
            PeriodoExecucao.ano.desc(), PeriodoExecucao.mes.desc()
        ).all()
        
        # Estatísticas
        stats = {
            'total_empresas': len(empresas),
            'total_atribuicoes_pendentes': len(atribuicoes),
            'total_periodos_ativos': len(periodos),
            'tarefas_concluidas_mes': AtribuicaoTarefa.query.filter_by(
                status='concluida'
            ).count() if usuario.tipo in ['admin', 'gerente'] else 0
        }
        
        return render_template('sistema_completo_dashboard.html',
                             usuario=usuario,
                             empresas=empresas,
                             atribuicoes=atribuicoes,
                             periodos=periodos,
                             stats=stats)
        
    except Exception as e:
        print(f"❌ Erro no dashboard: {str(e)}")
        return redirect(url_for('auth.login'))


@bp.get('/empresas')
def gerenciar_empresas():
    """Gerenciar empresas e suas tributações"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return redirect(url_for('auth.login_page'))
        
        usuario = Usuario.query.get(user_id)
        if not usuario or usuario.tipo not in ['admin', 'supervisor']:
            return redirect(url_for('auth.login'))
        
        empresas = Empresa.query.filter_by(ativo=True).order_by(Empresa.nome).all()
        tributacoes = Tributacao.query.all()
        
        return render_template('sistema_completo_empresas.html',
                             usuario=usuario,
                             empresas=empresas,
                             tributacoes=tributacoes)
        
    except Exception as e:
        print(f"❌ Erro ao carregar empresas: {str(e)}")
        return redirect(url_for('auth.login'))


@bp.get('/responsaveis-padrao')
def gerenciar_responsaveis_padrao():
    """Gerenciar responsáveis padrão por setor/tributação"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return redirect(url_for('auth.login_page'))
        
        usuario = Usuario.query.get(user_id)
        if not usuario or usuario.tipo not in ['admin', 'gerente']:
            return redirect(url_for('auth.login'))
        
        setores = Setor.query.all()
        tributacoes = Tributacao.query.all()
        tarefas = Tarefa.query.all()
        
        # Filtrar tarefas por setor se for gerente
        if usuario.tipo == 'gerente':
            tarefas = Tarefa.query.filter_by(setor_id=usuario.setor_id).all()
        
        responsaveis_padrao = ResponsavelPadraoTarefa.query.filter_by(ativo=True).all()
        
        return render_template('sistema_completo_responsaveis_padrao.html',
                             usuario=usuario,
                             setores=setores,
                             tributacoes=tributacoes,
                             tarefas=tarefas,
                             responsaveis_padrao=responsaveis_padrao)
        
    except Exception as e:
        print(f"❌ Erro ao carregar responsáveis padrão: {str(e)}")
        return redirect(url_for('auth.login'))


@bp.get('/atribuicoes')
def gerenciar_atribuicoes():
    """Gerenciar atribuições de tarefas"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return redirect(url_for('auth.login_page'))
        
        usuario = Usuario.query.get(user_id)
        if not usuario or usuario.tipo not in ['admin', 'gerente']:
            return redirect(url_for('auth.login'))
        
        empresas = Empresa.query.filter_by(ativo=True).order_by(Empresa.nome).all()
        periodos = PeriodoExecucao.query.filter_by(status='ativo').order_by(
            PeriodoExecucao.ano.desc(), PeriodoExecucao.mes.desc()
        ).all()
        
        # Filtrar atribuições por setor se for gerente
        if usuario.tipo == 'gerente':
            atribuicoes = AtribuicaoTarefa.query.join(Usuario).filter(
                Usuario.setor_id == usuario.setor_id
            ).order_by(AtribuicaoTarefa.criado_em.desc()).all()
        else:
            atribuicoes = AtribuicaoTarefa.query.order_by(
                AtribuicaoTarefa.criado_em.desc()
            ).all()
        
        return render_template('sistema_completo_atribuicoes.html',
                             usuario=usuario,
                             empresas=empresas,
                             periodos=periodos,
                             atribuicoes=atribuicoes)
        
    except Exception as e:
        print(f"❌ Erro ao carregar atribuições: {str(e)}")
        return redirect(url_for('auth.login'))


@bp.get('/minhas-tarefas')
def minhas_tarefas():
    """Tarefas do funcionário logado"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return redirect(url_for('auth.login_page'))
        
        usuario = Usuario.query.get(user_id)
        if not usuario or usuario.tipo != 'normal':
            return redirect(url_for('auth.login'))
        
        # Buscar atribuições do funcionário
        atribuicoes = AtribuicaoTarefa.query.filter_by(
            responsavel_id=user_id
        ).order_by(AtribuicaoTarefa.data_atribuicao.desc()).all()
        
        # Separar por status
        tarefas_pendentes = [a for a in atribuicoes if a.status == 'pendente']
        tarefas_em_andamento = [a for a in atribuicoes if a.status == 'em_andamento']
        tarefas_concluidas = [a for a in atribuicoes if a.status == 'concluida']
        tarefas_retificadas = [a for a in atribuicoes if a.status == 'retificada']
        
        return render_template('sistema_completo_minhas_tarefas.html',
                             usuario=usuario,
                             tarefas_pendentes=tarefas_pendentes,
                             tarefas_em_andamento=tarefas_em_andamento,
                             tarefas_concluidas=tarefas_concluidas,
                             tarefas_retificadas=tarefas_retificadas)
        
    except Exception as e:
        print(f"❌ Erro ao carregar minhas tarefas: {str(e)}")
        return redirect(url_for('auth.login'))


# ========================================
# APIs PARA O SISTEMA COMPLETO
# ========================================

@bp.post('/api/criar-periodo')
def api_criar_periodo():
    """API para criar período mensal para uma empresa"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'message': 'Usuário não autenticado'}), 401
        
        usuario = Usuario.query.get(user_id)
        if not usuario or usuario.tipo not in ['admin', 'supervisor']:
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
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'}), 500


@bp.post('/api/criar-responsavel-padrao')
def api_criar_responsavel_padrao():
    """API para criar responsável padrão"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'message': 'Usuário não autenticado'}), 401
        
        usuario = Usuario.query.get(user_id)
        if not usuario or usuario.tipo not in ['admin', 'gerente']:
            return jsonify({'success': False, 'message': 'Acesso negado'}), 403
        
        data = request.get_json()
        setor_id = data.get('setor_id')
        tributacao_id = data.get('tributacao_id')
        tarefa_id = data.get('tarefa_id')
        responsavel_id = data.get('responsavel_id')
        
        if not all([setor_id, tributacao_id, tarefa_id, responsavel_id]):
            return jsonify({'success': False, 'message': 'Dados obrigatórios não fornecidos'}), 400
        
        # Verificar se já existe
        responsavel_existente = ResponsavelPadraoTarefa.query.filter_by(
            setor_id=setor_id,
            tributacao_id=tributacao_id,
            tarefa_id=tarefa_id,
            responsavel_id=responsavel_id
        ).first()
        
        if responsavel_existente:
            return jsonify({'success': False, 'message': 'Responsável padrão já existe'}), 400
        
        responsavel_padrao = ResponsavelPadraoTarefa(
            setor_id=setor_id,
            tributacao_id=tributacao_id,
            tarefa_id=tarefa_id,
            responsavel_id=responsavel_id,
            ativo=True
        )
        
        db.session.add(responsavel_padrao)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Responsável padrão criado com sucesso!',
            'responsavel_id': responsavel_padrao.id
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'}), 500


@bp.post('/api/criar-atribuicoes-automaticas')
def api_criar_atribuicoes_automaticas():
    """API para criar atribuições automaticamente baseadas nos responsáveis padrão"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'message': 'Usuário não autenticado'}), 401
        
        usuario = Usuario.query.get(user_id)
        if not usuario or usuario.tipo not in ['admin', 'gerente']:
            return jsonify({'success': False, 'message': 'Acesso negado'}), 403
        
        data = request.get_json()
        empresa_id = data.get('empresa_id')
        periodo_id = data.get('periodo_id')
        tributacao_id = data.get('tributacao_id')
        
        if not all([empresa_id, periodo_id, tributacao_id]):
            return jsonify({'success': False, 'message': 'Dados obrigatórios não fornecidos'}), 400
        
        # Buscar responsáveis padrão para esta tributação
        responsaveis_padrao = ResponsavelPadraoTarefa.query.filter_by(
            tributacao_id=tributacao_id,
            ativo=True
        ).all()
        
        atribuicoes_criadas = 0
        
        for responsavel_padrao in responsaveis_padrao:
            # Verificar se já existe atribuição
            atribuicao_existente = AtribuicaoTarefa.query.filter_by(
                empresa_id=empresa_id,
                tributacao_id=tributacao_id,
                tarefa_id=responsavel_padrao.tarefa_id,
                responsavel_id=responsavel_padrao.responsavel_id,
                periodo_execucao_id=periodo_id
            ).first()
            
            if not atribuicao_existente:
                atribuicao = AtribuicaoTarefa(
                    empresa_id=empresa_id,
                    tributacao_id=tributacao_id,
                    tarefa_id=responsavel_padrao.tarefa_id,
                    responsavel_id=responsavel_padrao.responsavel_id,
                    periodo_execucao_id=periodo_id,
                    data_atribuicao=date.today(),
                    status='pendente'
                )
                
                db.session.add(atribuicao)
                atribuicoes_criadas += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'{atribuicoes_criadas} atribuições criadas com sucesso!',
            'atribuicoes_criadas': atribuicoes_criadas
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'}), 500


@bp.post('/api/executar-tarefa')
def api_executar_tarefa():
    """API para funcionário executar uma tarefa"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'message': 'Usuário não autenticado'}), 401
        
        usuario = Usuario.query.get(user_id)
        if not usuario or usuario.tipo != 'normal':
            return jsonify({'success': False, 'message': 'Acesso negado'}), 403
        
        data = request.get_json()
        atribuicao_id = data.get('atribuicao_id')
        status = data.get('status')  # 'concluida' ou 'retificada'
        observacoes = data.get('observacoes', '')
        
        if not atribuicao_id or not status:
            return jsonify({'success': False, 'message': 'Dados obrigatórios não fornecidos'}), 400
        
        # Verificar se a atribuição pertence ao usuário
        atribuicao = AtribuicaoTarefa.query.filter_by(
            id=atribuicao_id,
            responsavel_id=user_id
        ).first()
        
        if not atribuicao:
            return jsonify({'success': False, 'message': 'Atribuição não encontrada'}), 404
        
        # Criar execução
        execucao = ExecucaoTarefa(
            atribuicao_id=atribuicao_id,
            data_execucao=date.today(),
            status=status,
            observacoes=observacoes,
            confirmado_por=user_id,
            data_confirmacao=datetime.now()
        )
        
        db.session.add(execucao)
        
        # Atualizar status da atribuição
        if status == 'concluida':
            atribuicao.status = 'concluida'
        else:  # retificada
            atribuicao.status = 'retificada'
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Tarefa executada com sucesso!',
            'execucao_id': execucao.id
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'}), 500


@bp.get('/api/relatorio-execucao')
def api_relatorio_execucao():
    """API para relatório de execução"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'message': 'Usuário não autenticado'}), 401
        
        usuario = Usuario.query.get(user_id)
        if not usuario or usuario.tipo not in ['admin', 'gerente']:
            return jsonify({'success': False, 'message': 'Acesso negado'}), 403
        
        # Buscar estatísticas
        total_atribuicoes = AtribuicaoTarefa.query.count()
        atribuicoes_concluidas = AtribuicaoTarefa.query.filter_by(status='concluida').count()
        atribuicoes_pendentes = AtribuicaoTarefa.query.filter_by(status='pendente').count()
        atribuicoes_retificadas = AtribuicaoTarefa.query.filter_by(status='retificada').count()
        
        percentual_conclusao = (atribuicoes_concluidas * 100.0 / total_atribuicoes) if total_atribuicoes > 0 else 0
        
        relatorio = {
            'total_atribuicoes': total_atribuicoes,
            'atribuicoes_concluidas': atribuicoes_concluidas,
            'atribuicoes_pendentes': atribuicoes_pendentes,
            'atribuicoes_retificadas': atribuicoes_retificadas,
            'percentual_conclusao': round(percentual_conclusao, 2)
        }
        
        return jsonify({
            'success': True,
            'relatorio': relatorio
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'}), 500
