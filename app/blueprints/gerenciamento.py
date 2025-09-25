from flask import Blueprint, render_template, request, session, jsonify
from app.db import db
from app.models import Setor, Empresa, Usuario, Tarefa, RelacionamentoTarefa, Periodo
from datetime import datetime
import re

bp = Blueprint('gerenciamento', __name__, url_prefix='/gerenciamento')


def validate_period_format(period):
    """Valida se o período está no formato correto (MM/AAAA)"""
    pattern = r'^(0[1-9]|1[0-2])/(20[0-9]{2})$'
    return re.match(pattern, period) is not None


def convert_period_to_label(period):
    """Converte período de MM/AAAA para YYYY-MM"""
    if '/' in period:
        month, year = period.split('/')
        return f"{year}-{month.zfill(2)}"
    return period


@bp.get('')
@bp.get('/')
def return_page():
    """Página principal do painel do gerente"""
    try:
        # Parâmetros da requisição
        setor_atual = request.args.get('setor_id', type=int)
        periodo_input = request.args.get('periodo', '08/2025')
        empresa_atual = request.args.get('empresa_id', type=int)
        empresa_ids = request.args.get('empresa_ids', '')
        colaborador_id = request.args.get('colaborador_id', type=int)
        tarefa_id = request.args.get('tarefa_id', type=int)
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
        resultados = q.all()
        
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
            'colaboradores': colaboradores_data
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
        empresa_id = request.args.get('empresa_id', type=int)
        empresa_ids = request.args.get('empresa_ids', '')
        colaborador_id = request.args.get('colaborador_id', type=int)
        tarefa_id = request.args.get('tarefa_id', type=int)
        
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
            Periodo.periodo_label == periodo_atual,
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
        
        resultados = q.all()
        
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