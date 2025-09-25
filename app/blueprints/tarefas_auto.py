from flask import Blueprint, request, jsonify
from app.db import db
from app.models import Usuario, Empresa, Tarefa, RelacionamentoTarefa, Periodo, Retificacao
from datetime import datetime, date, timedelta
import calendar

bp = Blueprint('tarefas_auto', __name__, url_prefix='/api/tarefas-auto')


def gerar_periodo_label(ano, mes):
    """Gera o label do período no formato YYYY-MM"""
    return f"{ano}-{mes:02d}"


def calcular_datas_periodo(ano, mes, tipo_tarefa):
    """Calcula as datas de início e fim baseado no tipo da tarefa"""
    if tipo_tarefa == 'Mensal':
        inicio = date(ano, mes, 1)
        fim = date(ano, mes, calendar.monthrange(ano, mes)[1])
    elif tipo_tarefa == 'Trimestral':
        # Determina o trimestre
        trimestre = (mes - 1) // 3 + 1
        mes_inicio = (trimestre - 1) * 3 + 1
        mes_fim = trimestre * 3
        inicio = date(ano, mes_inicio, 1)
        fim = date(ano, mes_fim, calendar.monthrange(ano, mes_fim)[1])
        return inicio, fim, f"{ano}-T{trimestre}"
    elif tipo_tarefa == 'Anual':
        inicio = date(ano, 1, 1)
        fim = date(ano, 12, 31)
        return inicio, fim, f"{ano}-Anual"
    
    return inicio, fim, gerar_periodo_label(ano, mes)


@bp.post('/gerar-mes')
def gerar_tarefas_mes():
    """Gera tarefas para o mês atual ou especificado"""
    try:
        # Obter parâmetros
        ano = request.json.get('ano', datetime.now().year)
        mes = request.json.get('mes', datetime.now().month)
        
        # Verificar se já existem tarefas para este período
        periodo_label = gerar_periodo_label(ano, mes)
        periodos_existentes = Periodo.query.filter_by(periodo_label=periodo_label).count()
        
        if periodos_existentes > 0:
            return jsonify({
                'success': False,
                'message': f'Tarefas para {periodo_label} já foram geradas',
                'periodos_existentes': periodos_existentes
            })
        
        # Buscar todos os relacionamentos ativos
        relacionamentos = RelacionamentoTarefa.query.filter_by(status='ativa').all()
        
        tarefas_criadas = 0
        
        for rel in relacionamentos:
            tarefa = Tarefa.query.get(rel.tarefa_id)
            if not tarefa:
                continue
            
            # Calcular datas do período
            inicio, fim, periodo_label_tarefa = calcular_datas_periodo(ano, mes, tarefa.tipo)
            
            # Verificar se já existe período para este relacionamento
            periodo_existente = Periodo.query.filter_by(
                relacionamento_tarefa_id=rel.id,
                periodo_label=periodo_label_tarefa
            ).first()
            
            if periodo_existente:
                continue
            
            # Criar novo período
            novo_periodo = Periodo(
                relacionamento_tarefa_id=rel.id,
                inicio=inicio,
                fim=fim,
                periodo_label=periodo_label_tarefa,
                status='pendente',
                contador_retificacoes=0,
                atualizado_em=datetime.now()
            )
            
            db.session.add(novo_periodo)
            tarefas_criadas += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Tarefas geradas com sucesso para {periodo_label}',
            'tarefas_criadas': tarefas_criadas,
            'periodo': periodo_label
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Erro ao gerar tarefas: {str(e)}'
        }), 500


@bp.post('/concluir-tarefa')
def concluir_tarefa():
    """Conclui uma tarefa ou marca como retificada"""
    try:
        periodo_id = request.json.get('periodo_id')
        usuario_id = request.json.get('usuario_id')
        motivo_retificacao = request.json.get('motivo_retificacao', '')
        
        if not periodo_id or not usuario_id:
            return jsonify({
                'success': False,
                'message': 'ID do período e usuário são obrigatórios'
            }), 400
        
        periodo = Periodo.query.get(periodo_id)
        if not periodo:
            return jsonify({
                'success': False,
                'message': 'Período não encontrado'
            }), 404
        
        hoje = date.today()
        
        if periodo.status == 'pendente':
            # Primeira conclusão
            periodo.status = 'concluida'
            periodo.data_conclusao = hoje
            periodo.data_retificacao = None
            periodo.contador_retificacoes = 0
        else:
            # Retificação
            periodo.status = 'retificada'
            periodo.data_retificacao = hoje
            periodo.contador_retificacoes += 1
            
            # Criar registro de retificação
            retificacao = Retificacao(
                periodo_id=periodo_id,
                usuario_id=usuario_id,
                motivo=motivo_retificacao,
                criado_em=datetime.now()
            )
            db.session.add(retificacao)
        
        periodo.atualizado_em = datetime.now()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Tarefa atualizada com sucesso',
            'status': periodo.status,
            'data_conclusao': periodo.data_conclusao.isoformat() if periodo.data_conclusao else None,
            'data_retificacao': periodo.data_retificacao.isoformat() if periodo.data_retificacao else None,
            'contador_retificacoes': periodo.contador_retificacoes
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Erro ao atualizar tarefa: {str(e)}'
        }), 500


@bp.post('/reabrir-tarefa')
def reabrir_tarefa():
    """Reabre uma tarefa para nova conclusão"""
    try:
        periodo_id = request.json.get('periodo_id')
        
        if not periodo_id:
            return jsonify({
                'success': False,
                'message': 'ID do período é obrigatório'
            }), 400
        
        periodo = Periodo.query.get(periodo_id)
        if not periodo:
            return jsonify({
                'success': False,
                'message': 'Período não encontrado'
            }), 404
        
        periodo.status = 'pendente'
        periodo.atualizado_em = datetime.now()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Tarefa reaberta com sucesso',
            'status': periodo.status
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Erro ao reabrir tarefa: {str(e)}'
        }), 500


@bp.get('/verificar-geracao')
def verificar_geracao():
    """Verifica se as tarefas do mês atual foram geradas"""
    try:
        # Obter parâmetros opcionais
        ano = request.args.get('ano', type=int)
        mes = request.args.get('mes', type=int)
        
        # Usar mês atual se não especificado
        if not ano or not mes:
            hoje = datetime.now()
            ano = ano or hoje.year
            mes = mes or hoje.mes
        
        periodo_label = gerar_periodo_label(ano, mes)
        
        periodos_existentes = Periodo.query.filter_by(periodo_label=periodo_label).count()
        relacionamentos_ativos = RelacionamentoTarefa.query.filter_by(status='ativa').count()
        
        return jsonify({
            'success': True,
            'periodo_atual': periodo_label,
            'periodos_existentes': periodos_existentes,
            'relacionamentos_ativos': relacionamentos_ativos,
            'precisa_gerar': periodos_existentes == 0 and relacionamentos_ativos > 0
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro ao verificar geração: {str(e)}'
        }), 500


@bp.post('/gerar-tarefas-periodo')
def gerar_tarefas_periodo():
    """Gera tarefas para um período específico, incluindo novas tarefas vinculadas"""
    try:
        # Obter parâmetros
        ano = request.json.get('ano', datetime.now().year)
        mes = request.json.get('mes', datetime.now().month)
        
        # Calcular período
        periodo_label = gerar_periodo_label(ano, mes)
        
        # Buscar todos os relacionamentos ativos
        relacionamentos = RelacionamentoTarefa.query.filter_by(status='ativa').all()
        
        tarefas_criadas = 0
        tarefas_existentes = 0
        
        for rel in relacionamentos:
            tarefa = Tarefa.query.get(rel.tarefa_id)
            if not tarefa:
                continue
            
            # Calcular datas do período baseado no tipo da tarefa
            inicio, fim, periodo_label_tarefa = calcular_datas_periodo(ano, mes, tarefa.tipo)
            
            # Verificar se já existe período para este relacionamento
            periodo_existente = Periodo.query.filter_by(
                relacionamento_tarefa_id=rel.id,
                periodo_label=periodo_label_tarefa
            ).first()
            
            if periodo_existente:
                tarefas_existentes += 1
                continue
            
            # Criar novo período apenas se não existir
            novo_periodo = Periodo(
                relacionamento_tarefa_id=rel.id,
                inicio=inicio,
                fim=fim,
                periodo_label=periodo_label_tarefa,
                status='pendente',
                contador_retificacoes=0,
                atualizado_em=datetime.now()
            )
            
            db.session.add(novo_periodo)
            tarefas_criadas += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Verificação concluída para {periodo_label}',
            'tarefas_criadas': tarefas_criadas,
            'tarefas_existentes': tarefas_existentes,
            'periodo': periodo_label,
            'total_relacionamentos': len(relacionamentos)
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Erro ao gerar tarefas: {str(e)}'
        }), 500


@bp.get('/historico-retificacoes/<int:periodo_id>')
def historico_retificacoes(periodo_id):
    """Retorna o histórico de retificações de um período"""
    try:
        periodo = Periodo.query.get(periodo_id)
        if not periodo:
            return jsonify({
                'success': False,
                'message': 'Período não encontrado'
            }), 404
        
        retificacoes = Retificacao.query.filter_by(periodo_id=periodo_id).order_by(Retificacao.criado_em.desc()).all()
        
        historico = []
        for ret in retificacoes:
            usuario = Usuario.query.get(ret.usuario_id)
            historico.append({
                'id': ret.id,
                'usuario_nome': usuario.nome if usuario else 'N/A',
                'motivo': ret.motivo,
                'data': ret.criado_em.isoformat() if ret.criado_em else None
            })
        
        return jsonify({
            'success': True,
            'periodo_id': periodo_id,
            'contador_retificacoes': periodo.contador_retificacoes,
            'historico': historico
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro ao buscar histórico: {str(e)}'
        }), 500
