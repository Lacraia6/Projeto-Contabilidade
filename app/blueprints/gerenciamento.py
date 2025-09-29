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


def _should_show_task_by_type(tarefa_tipo, periodo_label, tarefa_periodo_label=None):
    """
    Determina se uma tarefa deve ser exibida baseado no seu tipo e período
    
    Args:
        tarefa_tipo (str): Tipo da tarefa (Mensal, Trimestral, Anual)
        periodo_label (str): Período filtrado pelo usuário (YYYY-MM)
        tarefa_periodo_label (str): Período da tarefa específica (YYYY-MM ou YYYY-TQ)
    
    Returns:
        bool: True se a tarefa deve ser exibida, False caso contrário
    """
    if tarefa_tipo == 'Mensal':
        return True  # Tarefas mensais aparecem todo mês
    
    elif tarefa_tipo == 'Trimestral':
        if not periodo_label or not tarefa_periodo_label:
            return False
        
        # Mapear trimestres para o mês final de cada trimestre
        trimestre_para_mes_final = {
            'T1': 3,   # Primeiro trimestre -> Março
            'T2': 6,   # Segundo trimestre -> Junho
            'T3': 9,   # Terceiro trimestre -> Setembro
            'T4': 12   # Quarto trimestre -> Dezembro
        }
        
        try:
            # Extrair mês do período filtrado pelo usuário
            if len(periodo_label) >= 7 and '-' in periodo_label:
                mes_filtro = int(periodo_label.split('-')[1])
                
                # Extrair trimestre da tarefa (ex: 2025-T3 -> T3)
                if tarefa_periodo_label and 'T' in tarefa_periodo_label:
                    trimestre_tarefa = tarefa_periodo_label.split('-')[-1]  # Pega a parte após o último '-'
                    
                    # Verificar se o mês filtrado é o mês final do trimestre da tarefa
                    mes_final_trimestre = trimestre_para_mes_final.get(trimestre_tarefa)
                    if mes_final_trimestre and mes_filtro == mes_final_trimestre:
                        return True
                
                return False
                
        except (ValueError, IndexError):
            return False
    
    elif tarefa_tipo == 'Anual':
        # Tarefas anuais aparecem o ano todo, mas serão tratadas separadamente
        return True
    
    return True  # Por padrão, mostrar a tarefa


@bp.get('')
@bp.get('/')
def return_page():
    """Página principal do painel do gerente"""
    try:
        # Parâmetros da requisição
        setor_atual = request.args.get('setor_id')
        if setor_atual:
            setor_atual = int(setor_atual)
        periodo_input = request.args.get('periodo', '08/2025')
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