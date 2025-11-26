from flask import Blueprint, render_template, request, session, jsonify, redirect, url_for
from app.db import db
from app.models import Empresa, Tributacao, Usuario, Checklist, ChecklistItem, ChecklistItemConclusao, ChecklistTemplate, ChecklistTemplateItem
from datetime import datetime
import re

bp = Blueprint('supervisor', __name__, url_prefix='/supervisor')


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
def index():
    """Página principal do painel do supervisor"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return redirect(url_for('auth.login'))
        
        # Verificar se é supervisor
        usuario = Usuario.query.get(user_id)
        if not usuario or usuario.tipo != 'supervisor':
            return redirect(url_for('auth.login'))
        
        # Buscar estatísticas
        total_empresas = Empresa.query.filter_by(ativo=True).count()
        total_checklists = Checklist.query.filter_by(ativo=True).count()
        total_usuarios = Usuario.query.filter_by(ativo=True).count()
        
        # Buscar empresas recentes
        empresas_recentes = Empresa.query.filter_by(ativo=True).order_by(Empresa.criado_em.desc()).limit(5).all()
        
        # Buscar checklists recentes
        checklists_recentes = Checklist.query.filter_by(ativo=True).order_by(Checklist.criado_em.desc()).limit(5).all()
        
        return render_template('supervisor.html',
                             total_empresas=total_empresas,
                             total_checklists=total_checklists,
                             total_usuarios=total_usuarios,
                             empresas_recentes=empresas_recentes,
                             checklists_recentes=checklists_recentes)
        
    except Exception as e:
        return render_template('supervisor.html', error=str(e))


@bp.get('/empresas')
def empresas():
    """Página de gerenciamento de empresas"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return redirect(url_for('auth.login'))
        
        # Verificar se é supervisor
        usuario = Usuario.query.get(user_id)
        if not usuario or usuario.tipo != 'supervisor':
            return redirect(url_for('auth.login'))
        
        # Buscar empresas
        empresas = Empresa.query.filter_by(ativo=True).order_by(Empresa.nome).all()
        
        # Buscar tributações
        tributacoes = Tributacao.query.all()
        
        return render_template('supervisor_empresas.html',
                             empresas=empresas,
                             tributacoes=tributacoes)
        
    except Exception as e:
        return render_template('supervisor_empresas.html', error=str(e))


@bp.post('/empresas/criar')
def criar_empresa():
    """Criar nova empresa"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'message': 'Usuário não autenticado'}), 401
        
        # Verificar se é supervisor
        usuario = Usuario.query.get(user_id)
        if not usuario or usuario.tipo != 'supervisor':
            return jsonify({'success': False, 'message': 'Acesso negado'}), 403
        
        data = request.get_json()
        codigo = data.get('codigo', '').strip()
        nome = data.get('nome', '').strip()
        tributacao_id = data.get('tributacao_id')
        
        # Validações
        if not codigo or not nome:
            return jsonify({'success': False, 'message': 'Código e nome são obrigatórios'}), 400
        
        # Verificar se código já existe
        if Empresa.query.filter_by(codigo=codigo).first():
            return jsonify({'success': False, 'message': 'Código da empresa já existe'}), 400
        
        # Criar empresa
        empresa = Empresa(
            codigo=codigo,
            nome=nome,
            tributacao_id=tributacao_id if tributacao_id else None,
            criado_em=datetime.now(),
            ativo=True
        )
        
        db.session.add(empresa)
        db.session.flush()  # Para obter o ID
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Empresa criada com sucesso!',
            'empresa_id': empresa.id,
            'empresa_nome': empresa.nome
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Erro ao criar empresa: {str(e)}'}), 500


@bp.post('/empresas/<int:empresa_id>/tributacao')
def alterar_tributacao(empresa_id):
    """Alterar tributação de uma empresa"""
    try:
        from app.models import RelacionamentoTarefa, Periodo, Tarefa, TarefaTributacao, VinculacaoEmpresaTributacao, MudancaTributacaoPendente
        from datetime import date
        from app.utils import gerar_periodo_label
        
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'message': 'Usuário não autenticado'}), 401
        
        # Verificar se é supervisor
        usuario = Usuario.query.get(user_id)
        if not usuario or usuario.tipo != 'supervisor':
            return jsonify({'success': False, 'message': 'Acesso negado'}), 403
        
        data = request.get_json()
        tributacao_id = data.get('tributacao_id')
        motivo = data.get('motivo', 'Mudança de tributação pelo supervisor')
        
        # Buscar empresa
        empresa = Empresa.query.get(empresa_id)
        if not empresa:
            return jsonify({'success': False, 'message': 'Empresa não encontrada'}), 404
        
        tributacao_anterior_id = empresa.tributacao_id
        
        # Verificar se a tributação está realmente mudando
        if tributacao_anterior_id == tributacao_id:
            return jsonify({'success': False, 'message': 'A empresa já possui esta tributação'}), 400
        
        # Identificar período atual
        hoje = date.today()
        periodo_atual_label = gerar_periodo_label(hoje.year, hoje.month)
        
        # Buscar todos os relacionamentos ativos da empresa
        relacionamentos_ativos = RelacionamentoTarefa.query.filter_by(
            empresa_id=empresa_id,
            versao_atual=True,
            status='ativa'
        ).all()
        
        # Separar relacionamentos: período atual vs futuros e tarefas comuns vs específicas
        relacionamentos_periodo_atual = []
        relacionamentos_futuros_com_tributacao = []
        
        for rel in relacionamentos_ativos:
            tarefa = Tarefa.query.get(rel.tarefa_id)
            if not tarefa:
                continue
            
            # Verificar se é tarefa comum (sem tributação específica)
            is_tarefa_comum = tarefa.tarefa_comum or (tarefa.tributacao_id is None and not TarefaTributacao.query.filter_by(tarefa_id=tarefa.id).first())
            
            # Se é tarefa comum, não desativar
            if is_tarefa_comum:
                continue
            
            # Verificar se tem período no período atual
            periodo_atual = Periodo.query.filter_by(
                relacionamento_tarefa_id=rel.id,
                periodo_label=periodo_atual_label
            ).first()
            
            if periodo_atual and periodo_atual.status not in ['concluida', 'cancelada']:
                # Tem período ativo, não desativar
                relacionamentos_periodo_atual.append(rel)
            else:
                # Não tem período ativo ou já concluído, pode desativar para próximos períodos
                # Verificar se a tarefa é da tributação anterior
                if tributacao_anterior_id:
                    # Verificar se tarefa pertence à tributação anterior
                    tarefa_trib = TarefaTributacao.query.filter_by(
                        tarefa_id=tarefa.id,
                        tributacao_id=tributacao_anterior_id
                    ).first()
                    
                    if tarefa_trib or tarefa.tributacao_id == tributacao_anterior_id:
                        relacionamentos_futuros_com_tributacao.append(rel)
        
        # Desativar relacionamentos de tarefas da tributação antiga (apenas para próximos períodos)
        for rel in relacionamentos_futuros_com_tributacao:
            rel.versao_atual = False
            rel.data_fim = date.today()
            rel.motivo_desativacao = f"Mudança de tributação: próximos períodos desativados (período atual preservado)"
        
        # Criar ou atualizar vinculação empresa-tributação
        if tributacao_id:
            # Desativar vinculação atual se existir
            vinculacao_atual = VinculacaoEmpresaTributacao.query.filter_by(
                empresa_id=empresa_id,
                ativo=True
            ).first()
            
            if vinculacao_atual:
                vinculacao_atual.ativo = False
                vinculacao_atual.data_fim = date.today()
            
            # Criar nova vinculação
            nova_vinculacao = VinculacaoEmpresaTributacao(
                empresa_id=empresa_id,
                tributacao_id=tributacao_id,
                data_inicio=date.today(),
                ativo=True
            )
            db.session.add(nova_vinculacao)
            db.session.flush()  # Para obter o ID
            
            # Buscar tarefas da nova tributação
            tarefas_nova_tributacao = TarefaTributacao.query.filter_by(
                tributacao_id=tributacao_id,
                ativo=True
            ).all()
            
            # Buscar também tarefas com tributacao_id direto
            tarefas_diretas = Tarefa.query.filter_by(
                tributacao_id=tributacao_id
            ).all()
            
            # Criar relacionamentos para novas tarefas (sem responsável - será definido pelo gerente)
            tarefas_ids_processadas = set()
            
            for tt in tarefas_nova_tributacao:
                if tt.tarefa_id in tarefas_ids_processadas:
                    continue
                tarefas_ids_processadas.add(tt.tarefa_id)
                
                # Verificar se já existe relacionamento desativado (para reativar)
                rel_existente = RelacionamentoTarefa.query.filter_by(
                    empresa_id=empresa_id,
                    tarefa_id=tt.tarefa_id,
                    versao_atual=False
                ).order_by(RelacionamentoTarefa.criado_em.desc()).first()
                
                if rel_existente:
                    # Reativar relacionamento existente
                    rel_existente.versao_atual = True
                    rel_existente.vinculacao_id = nova_vinculacao.id
                    rel_existente.data_inicio = date.today()
                    rel_existente.data_fim = None
                    rel_existente.motivo_desativacao = None
                    rel_existente.responsavel_id = None  # Será definido pelo gerente
                    rel_existente.status = 'ativa'
                else:
                    # Criar novo relacionamento (sem responsável)
                    novo_rel = RelacionamentoTarefa(
                        empresa_id=empresa_id,
                        tarefa_id=tt.tarefa_id,
                        responsavel_id=None,  # Será definido pelo gerente
                        vinculacao_id=nova_vinculacao.id,
                        status='ativa',
                        data_inicio=date.today(),
                        versao_atual=True
                    )
                    db.session.add(novo_rel)
            
            # Processar tarefas com tributacao_id direto
            for tarefa in tarefas_diretas:
                if tarefa.id in tarefas_ids_processadas:
                    continue
                tarefas_ids_processadas.add(tarefa.id)
                
                # Verificar se já existe relacionamento desativado
                rel_existente = RelacionamentoTarefa.query.filter_by(
                    empresa_id=empresa_id,
                    tarefa_id=tarefa.id,
                    versao_atual=False
                ).order_by(RelacionamentoTarefa.criado_em.desc()).first()
                
                if rel_existente:
                    rel_existente.versao_atual = True
                    rel_existente.vinculacao_id = nova_vinculacao.id
                    rel_existente.data_inicio = date.today()
                    rel_existente.data_fim = None
                    rel_existente.motivo_desativacao = None
                    rel_existente.responsavel_id = None
                    rel_existente.status = 'ativa'
                else:
                    novo_rel = RelacionamentoTarefa(
                        empresa_id=empresa_id,
                        tarefa_id=tarefa.id,
                        responsavel_id=None,
                        vinculacao_id=nova_vinculacao.id,
                        status='ativa',
                        data_inicio=date.today(),
                        versao_atual=True
                    )
                    db.session.add(novo_rel)
            
            # Criar registro de mudança pendente para notificação dos gerentes
            mudanca_pendente = MudancaTributacaoPendente(
                empresa_id=empresa_id,
                tributacao_anterior_id=tributacao_anterior_id,
                tributacao_nova_id=tributacao_id,
                data_mudanca=date.today(),
                motivo=motivo,
                status='pendente',
                criado_por=user_id
            )
            db.session.add(mudanca_pendente)
        
        # Atualizar empresa
        empresa.tributacao_id = tributacao_id if tributacao_id else None
        empresa.atualizado_em = datetime.now()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Tributação alterada com sucesso! Tarefas do período atual foram preservadas. As novas tarefas aparecerão para vinculação no painel do gerente.',
            'mudanca_id': mudanca_pendente.id if tributacao_id else None
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Erro ao alterar tributação: {str(e)}'}), 500


@bp.get('/checklists')
def checklists():
    """Página de gerenciamento de checklists"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return redirect(url_for('auth.login'))
        
        # Verificar se é supervisor
        usuario = Usuario.query.get(user_id)
        if not usuario or usuario.tipo != 'supervisor':
            return redirect(url_for('auth.login'))
        
        # Buscar checklists
        checklists = Checklist.query.filter_by(ativo=True).order_by(Checklist.criado_em.desc()).all()
        
        return render_template('supervisor_checklists.html', checklists=checklists)
        
    except Exception as e:
        return render_template('supervisor_checklists.html', error=str(e))


@bp.get('/checklists/criar')
def criar_checklist_page():
    """Página para criar checklist"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return redirect(url_for('auth.login'))
        
        # Verificar se é supervisor
        usuario = Usuario.query.get(user_id)
        if not usuario or usuario.tipo != 'supervisor':
            return redirect(url_for('auth.login'))
        
        # Buscar empresas
        empresas = Empresa.query.filter_by(ativo=True).order_by(Empresa.nome).all()
        
        # Buscar usuários
        usuarios = Usuario.query.filter_by(ativo=True, tipo='normal').order_by(Usuario.nome).all()
        
        return render_template('supervisor_criar_checklist.html',
                             empresas=empresas,
                             usuarios=usuarios)
        
    except Exception as e:
        return render_template('supervisor_criar_checklist.html', error=str(e))


@bp.post('/checklists/criar')
def criar_checklist():
    """Criar novo checklist"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'message': 'Usuário não autenticado'}), 401
        
        # Verificar se é supervisor
        usuario = Usuario.query.get(user_id)
        if not usuario or usuario.tipo != 'supervisor':
            return jsonify({'success': False, 'message': 'Acesso negado'}), 403
        
        data = request.get_json()
        empresa_id = data.get('empresa_id')
        nome = data.get('nome', '').strip()
        descricao = data.get('descricao', '').strip()
        itens = data.get('itens', [])
        
        # Validações
        if not empresa_id or not nome:
            return jsonify({'success': False, 'message': 'Empresa e nome são obrigatórios'}), 400
        
        if not itens:
            return jsonify({'success': False, 'message': 'Pelo menos um item é obrigatório'}), 400
        
        # Verificar se empresa existe
        empresa = Empresa.query.get(empresa_id)
        if not empresa:
            return jsonify({'success': False, 'message': 'Empresa não encontrada'}), 404
        
        # Criar checklist
        checklist = Checklist(
            empresa_id=empresa_id,
            nome=nome,
            descricao=descricao,
            criado_por=user_id,
            criado_em=datetime.now(),
            ativo=True
        )
        
        db.session.add(checklist)
        db.session.flush()  # Para obter o ID
        
        # Criar itens do checklist
        for i, item_data in enumerate(itens):
            item = ChecklistItem(
                checklist_id=checklist.id,
                titulo=item_data.get('titulo', '').strip(),
                descricao=item_data.get('descricao', '').strip(),
                ordem=i + 1,
                responsavel_id=item_data.get('responsavel_id'),
                obrigatorio=item_data.get('obrigatorio', True),
                ativo=True
            )
            db.session.add(item)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Checklist criado com sucesso!',
            'checklist_id': checklist.id
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Erro ao criar checklist: {str(e)}'}), 500


@bp.get('/checklists/<int:checklist_id>')
def visualizar_checklist(checklist_id):
    """Visualizar checklist específico"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return redirect(url_for('auth.login'))
        
        # Verificar se é supervisor
        usuario = Usuario.query.get(user_id)
        if not usuario or usuario.tipo != 'supervisor':
            return redirect(url_for('auth.login'))
        
        # Buscar checklist
        checklist = Checklist.query.get(checklist_id)
        if not checklist:
            return render_template('supervisor_checklist_detalhes.html', error='Checklist não encontrado')
        
        return render_template('supervisor_checklist_detalhes.html', checklist=checklist)
        
    except Exception as e:
        return render_template('supervisor_checklist_detalhes.html', error=str(e))


# APIs para o painel de usuários
@bp.get('/api/usuarios')
def api_usuarios():
    """API para buscar usuários"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'message': 'Usuário não autenticado'}), 401
        
        # Verificar se é supervisor
        usuario = Usuario.query.get(user_id)
        if not usuario or usuario.tipo != 'supervisor':
            return jsonify({'success': False, 'message': 'Acesso negado'}), 403
        
        # Buscar usuários
        usuarios = Usuario.query.filter_by(ativo=True, tipo='normal').order_by(Usuario.nome).all()
        
        usuarios_data = []
        for u in usuarios:
            usuarios_data.append({
                'id': u.id,
                'nome': u.nome,
                'login': u.login,
                'setor': u.setor.nome if u.setor else 'Sem setor'
            })
        
        return jsonify({'success': True, 'usuarios': usuarios_data})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro ao buscar usuários: {str(e)}'}), 500


@bp.get('/api/empresas')
def api_empresas_search():
    """API para buscar empresas com filtro de texto"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'message': 'Usuário não autenticado'}), 401
        
        # Verificar se é supervisor
        usuario = Usuario.query.get(user_id)
        if not usuario or usuario.tipo != 'supervisor':
            return jsonify({'success': False, 'message': 'Acesso negado'}), 403
        
        # Parâmetro de busca
        query = request.args.get('q', '').strip()
        
        if not query:
            return jsonify({'success': True, 'empresas': []})
        
        # Buscar empresas que contenham o texto
        empresas = Empresa.query.filter(
            Empresa.ativo == True,
            (Empresa.nome.contains(query) | Empresa.codigo.contains(query))
        ).order_by(Empresa.nome).limit(10).all()
        
        empresas_data = []
        for e in empresas:
            empresas_data.append({
                'id': e.id,
                'codigo': e.codigo,
                'nome': e.nome,
                'tributacao': e.tributacao.nome if e.tributacao else 'Sem tributação'
            })
        
        return jsonify({'success': True, 'empresas': empresas_data})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro ao buscar empresas: {str(e)}'}), 500




# ===== ROTAS PARA TEMPLATES DE CHECKLIST =====

@bp.get('/templates')
def templates():
    """Página de gerenciamento de templates de checklist"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return redirect(url_for('auth.login'))
        
        # Verificar se é supervisor
        usuario = Usuario.query.get(user_id)
        if not usuario or usuario.tipo != 'supervisor':
            return redirect(url_for('auth.login'))
        
        # Buscar templates
        templates = ChecklistTemplate.query.filter_by(ativo=True).order_by(ChecklistTemplate.criado_em.desc()).all()
        
        return render_template('supervisor_templates.html', templates=templates)
        
    except Exception as e:
        return render_template('supervisor_templates.html', templates=[], error=str(e))


@bp.get('/templates/criar')
def criar_template():
    """Página para criar novo template"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return redirect(url_for('auth.login'))
        
        # Verificar se é supervisor
        usuario = Usuario.query.get(user_id)
        if not usuario or usuario.tipo != 'supervisor':
            return redirect(url_for('auth.login'))
        
        return render_template('supervisor_criar_template.html')
        
    except Exception as e:
        return render_template('supervisor_criar_template.html', error=str(e))


@bp.post('/templates/criar')
def criar_template_post():
    """Criar novo template de checklist"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'message': 'Usuário não autenticado'}), 401
        
        # Verificar se é supervisor
        usuario = Usuario.query.get(user_id)
        if not usuario or usuario.tipo != 'supervisor':
            return jsonify({'success': False, 'message': 'Acesso negado'}), 403
        
        # Dados do formulário
        nome = request.form.get('nome', '').strip()
        descricao = request.form.get('descricao', '').strip()
        categoria = request.form.get('categoria', '').strip()
        
        if not nome:
            return jsonify({'success': False, 'message': 'Nome do template é obrigatório'}), 400
        
        # Criar template
        template = ChecklistTemplate(
            nome=nome,
            descricao=descricao,
            categoria=categoria,
            criado_por=user_id
        )
        
        db.session.add(template)
        db.session.flush()  # Para obter o ID
        
        # Processar itens do template
        itens_data = request.form.get('itens', '')
        if itens_data:
            import json
            try:
                itens = json.loads(itens_data)
                for i, item in enumerate(itens):
                    if item.get('titulo', '').strip():
                        template_item = ChecklistTemplateItem(
                            template_id=template.id,
                            titulo=item['titulo'].strip(),
                            descricao=item.get('descricao', '').strip(),
                            ordem=i + 1,
                            obrigatorio=item.get('obrigatorio', True)
                        )
                        db.session.add(template_item)
            except json.JSONDecodeError:
                pass  # Se não conseguir decodificar, continua sem itens
        
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': 'Template criado com sucesso!',
            'template_id': template.id
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Erro ao criar template: {str(e)}'}), 500


@bp.get('/templates/<int:template_id>')
def visualizar_template(template_id):
    """Visualizar template específico"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return redirect(url_for('auth.login'))
        
        # Verificar se é supervisor
        usuario = Usuario.query.get(user_id)
        if not usuario or usuario.tipo != 'supervisor':
            return redirect(url_for('auth.login'))
        
        # Buscar template
        template = ChecklistTemplate.query.get_or_404(template_id)
        
        return render_template('supervisor_visualizar_template.html', template=template)
        
    except Exception as e:
        return render_template('supervisor_visualizar_template.html', template=None, error=str(e))


@bp.post('/templates/<int:template_id>/aplicar')
def aplicar_template(template_id):
    """Aplicar template a uma empresa"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'message': 'Usuário não autenticado'}), 401
        
        # Verificar se é supervisor
        usuario = Usuario.query.get(user_id)
        if not usuario or usuario.tipo != 'supervisor':
            return jsonify({'success': False, 'message': 'Acesso negado'}), 403
        
        # Buscar template
        template = ChecklistTemplate.query.get_or_404(template_id)
        
        # Dados do formulário
        empresa_id = request.form.get('empresa_id')
        if not empresa_id:
            return jsonify({'success': False, 'message': 'Empresa é obrigatória'}), 400
        
        # Verificar se empresa existe
        empresa = Empresa.query.get(empresa_id)
        if not empresa:
            return jsonify({'success': False, 'message': 'Empresa não encontrada'}), 404
        
        # Criar checklist baseado no template
        checklist = Checklist(
            empresa_id=empresa_id,
            nome=f"{template.nome} - {empresa.nome}",
            descricao=template.descricao,
            criado_por=user_id
        )
        
        db.session.add(checklist)
        db.session.flush()  # Para obter o ID
        
        # Processar responsáveis dos itens
        responsaveis_data = request.form.get('responsaveis', '')
        responsaveis = {}
        if responsaveis_data:
            import json
            try:
                responsaveis = json.loads(responsaveis_data)
            except json.JSONDecodeError:
                pass
        
        # Criar itens do checklist baseados no template
        for template_item in template.itens:
            if template_item.ativo:
                # Buscar responsável para este item
                responsavel_id = responsaveis.get(str(template_item.id))
                if not responsavel_id:
                    # Se não especificado, usar o criador do checklist
                    responsavel_id = user_id
                
                checklist_item = ChecklistItem(
                    checklist_id=checklist.id,
                    titulo=template_item.titulo,
                    descricao=template_item.descricao,
                    ordem=template_item.ordem,
                    responsavel_id=responsavel_id,
                    obrigatorio=template_item.obrigatorio
                )
                db.session.add(checklist_item)
        
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': f'Checklist criado com sucesso para {empresa.nome}!',
            'checklist_id': checklist.id
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Erro ao aplicar template: {str(e)}'}), 500


@bp.get('/api/templates')
def api_templates():
    """API para buscar templates"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'message': 'Usuário não autenticado'}), 401
        
        # Verificar se é supervisor
        usuario = Usuario.query.get(user_id)
        if not usuario or usuario.tipo != 'supervisor':
            return jsonify({'success': False, 'message': 'Acesso negado'}), 403
        
        # Buscar templates
        templates = ChecklistTemplate.query.filter_by(ativo=True).order_by(ChecklistTemplate.nome).all()
        
        templates_data = []
        for template in templates:
            templates_data.append({
                'id': template.id,
                'nome': template.nome,
                'descricao': template.descricao,
                'categoria': template.categoria,
                'itens_count': len(template.itens),
                'criado_em': template.criado_em.strftime('%d/%m/%Y') if template.criado_em else ''
            })
        
        return jsonify({'success': True, 'templates': templates_data})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro ao buscar templates: {str(e)}'}), 500


@bp.get('/api/templates/<int:template_id>')
def api_template_detalhes(template_id):
    """API para buscar detalhes de um template"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'message': 'Usuário não autenticado'}), 401
        
        # Verificar se é supervisor
        usuario = Usuario.query.get(user_id)
        if not usuario or usuario.tipo != 'supervisor':
            return jsonify({'success': False, 'message': 'Acesso negado'}), 403
        
        # Buscar template
        template = ChecklistTemplate.query.get_or_404(template_id)
        
        # Buscar usuários para seleção de responsáveis
        usuarios = Usuario.query.filter_by(ativo=True).order_by(Usuario.nome).all()
        
        template_data = {
            'id': template.id,
            'nome': template.nome,
            'descricao': template.descricao,
            'categoria': template.categoria,
            'itens': []
        }
        
        for item in template.itens:
            if item.ativo:
                template_data['itens'].append({
                    'id': item.id,
                    'titulo': item.titulo,
                    'descricao': item.descricao,
                    'ordem': item.ordem,
                    'obrigatorio': item.obrigatorio
                })
        
        usuarios_data = []
        for user in usuarios:
            usuarios_data.append({
                'id': user.id,
                'nome': user.nome,
                'tipo': user.tipo
            })
        
        return jsonify({
            'success': True, 
            'template': template_data,
            'usuarios': usuarios_data
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro ao buscar template: {str(e)}'}), 500


@bp.delete('/templates/<int:template_id>')
def excluir_template(template_id):
    """Excluir template de checklist"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'message': 'Usuário não autenticado'}), 401
        
        # Verificar se é supervisor
        usuario = Usuario.query.get(user_id)
        if not usuario or usuario.tipo != 'supervisor':
            return jsonify({'success': False, 'message': 'Acesso negado'}), 403
        
        # Buscar template
        template = ChecklistTemplate.query.get_or_404(template_id)
        
        # Verificar se o template foi criado pelo usuário atual ou se é admin
        if template.criado_por != user_id and usuario.tipo != 'admin':
            return jsonify({'success': False, 'message': 'Você só pode excluir templates criados por você'}), 403
        
        # Verificar se há checklists usando este template
        # (Por enquanto, vamos apenas marcar como inativo)
        template.ativo = False
        
        # Marcar itens como inativos também
        for item in template.itens:
            item.ativo = False
        
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': f'Template "{template.nome}" excluído com sucesso!'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Erro ao excluir template: {str(e)}'}), 500
