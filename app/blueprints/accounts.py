from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app.db import db
from app.models import Setor, Tributacao, Empresa, Usuario, Tarefa, RelacionamentoTarefa

bp = Blueprint('accounts', __name__, url_prefix='/tarefas')


@bp.get('')
@bp.get('/')
@bp.get('/page')
def return_page():
	setores = Setor.query.all()
	tributacoes = Tributacao.query.all()
	empresas = Empresa.query.order_by(Empresa.nome).all()
	usuarios = Usuario.query.order_by(Usuario.nome).all()

	# tarefas com nomes
	tarefas = []
	for t in Tarefa.query.all():
		setor = next((s for s in setores if s.id == t.setor_id), None)
		trib = next((tr for tr in tributacoes if tr.id == t.tributacao_id), None)
		tarefas.append({
			"id": t.id,
			"nome": t.nome,
			"tipo": t.tipo,
			"descricao": t.descricao,
			"setor_id": t.setor_id,
			"setor_nome": setor.nome if setor else '-',
			"tributacao_id": t.tributacao_id,
			"tributacao_nome": trib.nome if trib else '-',
		})

	# relacionamentos
	rels = []
	for r in RelacionamentoTarefa.query.all():
		emp = next((e for e in empresas if e.id == r.empresa_id), None)
		tarefa = Tarefa.query.get(r.tarefa_id)
		resp = Usuario.query.get(r.responsavel_id) if r.responsavel_id else None
		rels.append({
			"id": r.id,
			"empresa_nome": emp.nome if emp else '-',
			"tarefa_nome": tarefa.nome if tarefa else '-',
			"responsavel_nome": resp.nome if resp else None,
			"responsavel_id": r.responsavel_id,
			"status": r.status,
			"dia_vencimento": r.dia_vencimento,
			"prazo_especifico": r.prazo_especifico.isoformat() if r.prazo_especifico else None,
		})

	return render_template(
		'accounts.html',
		aba='contas',
		setores=setores,
		tributacoes=tributacoes,
		empresas=empresas,
		usuarios=usuarios,
		tarefas=tarefas,
		rels=rels,
	)


@bp.post('/create')
def create_task():
	t = Tarefa(
		nome=request.form.get('nome'),
		tipo=request.form.get('tipo'),
		descricao=request.form.get('descricao'),
		tributacao_id=request.form.get('tributacao_id', type=int),
		setor_id=request.form.get('setor_id', type=int)
	)
	db.session.add(t)
	db.session.commit()
	flash('Tarefa criada com sucesso!')
	return redirect(url_for('accounts.return_page'))


@bp.post('/edit')
def edit_task():
	tid = request.form.get('id', type=int)
	t = Tarefa.query.get(tid)
	if t:
		t.nome = request.form.get('nome')
		t.tipo = request.form.get('tipo')
		t.descricao = request.form.get('descricao')
		t.setor_id = request.form.get('setor_id', type=int)
		t.tributacao_id = request.form.get('tributacao_id', type=int)
		db.session.commit()
		flash('Tarefa atualizada!')
	return redirect(url_for('accounts.return_page'))


@bp.post('/delete')
def delete_task():
	tid = request.form.get('id', type=int)
	t = Tarefa.query.get(tid)
	if t:
		db.session.delete(t)
		db.session.commit()
		flash('Tarefa excluída!')
	return redirect(url_for('accounts.return_page'))


@bp.post('/link')
def link_task():
	rel = RelacionamentoTarefa(
		empresa_id=request.form.get('empresa_id', type=int),
		tarefa_id=request.form.get('tarefa_id', type=int),
		responsavel_id=request.form.get('responsavel_id', type=int),
		status='ativa',
		dia_vencimento=request.form.get('dia_vencimento', type=int),
		prazo_especifico=request.form.get('prazo_especifico') or None,
	)
	db.session.add(rel)
	db.session.commit()
	flash('Vínculo criado!')
	return redirect(url_for('accounts.return_page'))


@bp.post('/edit-link')
def edit_link():
	rid = request.form.get('id', type=int)
	r = RelacionamentoTarefa.query.get(rid)
	if r:
		r.status = request.form.get('status')
		r.responsavel_id = request.form.get('responsavel_id', type=int)
		r.dia_vencimento = request.form.get('dia_vencimento', type=int)
		r.prazo_especifico = request.form.get('prazo_especifico') or None
		db.session.commit()
		flash('Vínculo atualizado!')
	return redirect(url_for('accounts.return_page'))


@bp.post('/delete-link')
def delete_link():
	rid = request.form.get('id', type=int)
	r = RelacionamentoTarefa.query.get(rid)
	if r:
		db.session.delete(r)
		db.session.commit()
		flash('Vínculo excluído!')
	return redirect(url_for('accounts.return_page'))


# =====================
# Vinculação em Massa
# =====================

@bp.post('/bulk-link')
def bulk_link_tasks():
	"""Vincula múltiplas tarefas a múltiplas empresas"""
	empresa_ids = request.form.getlist('empresa_ids')
	tarefa_ids = request.form.getlist('tarefa_ids')
	responsavel_id = request.form.get('responsavel_id', type=int)
	dia_vencimento = request.form.get('dia_vencimento', type=int)
	
	# Processar IDs - pode vir como lista ou string separada por vírgulas
	def process_ids(ids_list):
		result = []
		for id_item in ids_list:
			if id_item.strip():
				# Se contém vírgula, dividir e adicionar cada ID
				if ',' in id_item:
					split_ids = [id_str.strip() for id_str in id_item.split(',') if id_str.strip()]
					result.extend([int(id_str) for id_str in split_ids])
				else:
					# ID único
					result.append(int(id_item))
		return result
	
	empresa_ids = process_ids(empresa_ids)
	tarefa_ids = process_ids(tarefa_ids)
	
	# Se nenhuma empresa foi selecionada, usar todas as empresas ativas
	if not empresa_ids:
		empresas_ativas = Empresa.query.filter_by(ativo=True).all()
		empresa_ids = [empresa.id for empresa in empresas_ativas]
	
	if not tarefa_ids:
		flash('Selecione pelo menos uma tarefa!')
		return redirect(url_for('accounts.return_page'))
	
	vinculos_criados = 0
	for empresa_id in empresa_ids:
		for tarefa_id in tarefa_ids:
			# Verifica se já existe o vínculo
			existing = RelacionamentoTarefa.query.filter_by(
				empresa_id=empresa_id, 
				tarefa_id=tarefa_id
			).first()
			
			if not existing:
				rel = RelacionamentoTarefa(
					empresa_id=empresa_id,
					tarefa_id=tarefa_id,
					responsavel_id=responsavel_id,
					status='ativa',
					dia_vencimento=dia_vencimento
				)
				db.session.add(rel)
				vinculos_criados += 1
	
	db.session.commit()
	flash(f'Criados {vinculos_criados} vínculos com sucesso!')
	return redirect(url_for('accounts.return_page'))


@bp.post('/sector-link')
def sector_link_tasks():
	"""Vincula todas as tarefas de um setor a todas as empresas de uma tributação"""
	setor_id = request.form.get('setor_id', type=int)
	tributacao_id = request.form.get('tributacao_id', type=int)
	responsavel_id = request.form.get('responsavel_id', type=int)
	dia_vencimento = request.form.get('dia_vencimento', type=int)
	
	if not setor_id or not tributacao_id:
		flash('Selecione um setor e uma tributação!')
		return redirect(url_for('accounts.return_page'))
	
	# Busca tarefas do setor
	tarefas = Tarefa.query.filter_by(setor_id=setor_id).all()
	# Busca empresas da tributação
	empresas = Empresa.query.filter_by(tributacao_id=tributacao_id).all()
	
	if not tarefas or not empresas:
		flash('Nenhuma tarefa encontrada para o setor ou nenhuma empresa para a tributação!')
		return redirect(url_for('accounts.return_page'))
	
	vinculos_criados = 0
	for empresa in empresas:
		for tarefa in tarefas:
			# Verifica se já existe o vínculo
			existing = RelacionamentoTarefa.query.filter_by(
				empresa_id=empresa.id, 
				tarefa_id=tarefa.id
			).first()
			
			if not existing:
				rel = RelacionamentoTarefa(
					empresa_id=empresa.id,
					tarefa_id=tarefa.id,
					responsavel_id=responsavel_id,
					status='ativa',
					dia_vencimento=dia_vencimento
				)
				db.session.add(rel)
				vinculos_criados += 1
	
	db.session.commit()
	flash(f'Criados {vinculos_criados} vínculos entre {len(tarefas)} tarefas e {len(empresas)} empresas!')
	return redirect(url_for('accounts.return_page'))


@bp.post('/bulk-delete-links')
def bulk_delete_links():
	"""Remove múltiplos vínculos"""
	link_ids = request.form.getlist('link_ids')
	
	if not link_ids:
		flash('Selecione pelo menos um vínculo para remover!')
		return redirect(url_for('accounts.return_page'))
	
	deleted_count = 0
	for link_id in link_ids:
		r = RelacionamentoTarefa.query.get(int(link_id))
		if r:
			db.session.delete(r)
			deleted_count += 1
	
	db.session.commit()
	flash(f'Removidos {deleted_count} vínculos!')
	return redirect(url_for('accounts.return_page'))


# =====================
# Endpoints AJAX para Busca
# =====================

@bp.get('/api/empresas')
def api_empresas():
	"""Endpoint AJAX para buscar empresas"""
	search = request.args.get('search', '').strip()
	limit = request.args.get('limit', 50, type=int)
	
	try:
		query = Empresa.query.filter(Empresa.ativo == True)
		
		if search:
			query = query.filter(
				(Empresa.nome.contains(search)) | 
				(Empresa.codigo.contains(search))
			)
		
		empresas = query.order_by(Empresa.nome).limit(limit).all()
		
		return jsonify({
			'empresas': [
				{
					'id': e.id,
					'nome': e.nome,
					'codigo': e.codigo,
					'tributacao_nome': e.tributacao.nome if e.tributacao else 'N/A'
				}
				for e in empresas
			]
		})
	except Exception as e:
		print(f"Erro na busca de empresas: {e}")
		return {'empresas': [], 'error': str(e)}


@bp.get('/api/tarefas')
def api_tarefas():
	"""Endpoint AJAX para buscar tarefas"""
	search = request.args.get('search', '').strip()
	setor_id = request.args.get('setor_id', type=int)
	limit = request.args.get('limit', 50, type=int)
	
	try:
		query = Tarefa.query
		
		if search:
			query = query.filter(Tarefa.nome.contains(search))
		
		if setor_id:
			query = query.filter(Tarefa.setor_id == setor_id)
		
		tarefas = query.order_by(Tarefa.nome).limit(limit).all()
		
		return jsonify({
			'tarefas': [
				{
					'id': t.id,
					'nome': t.nome,
					'tipo': t.tipo,
					'setor_nome': t.setor.nome if t.setor else 'N/A',
					'tributacao_nome': t.tributacao.nome if t.tributacao else 'N/A'
				}
				for t in tarefas
			]
		})
	except Exception as e:
		print(f"Erro na busca de tarefas: {e}")
		return {'tarefas': [], 'error': str(e)}


@bp.get('/api/usuarios-setor')
def api_usuarios_setor():
	"""Endpoint AJAX para buscar usuários por setor"""
	setor_id = request.args.get('setor_id', type=int)
	
	# Se não há setor_id, retornar todos os usuários ativos
	if not setor_id:
		usuarios = Usuario.query.filter_by(ativo=True).order_by(Usuario.nome).all()
	else:
		usuarios = Usuario.query.filter_by(setor_id=setor_id, ativo=True).order_by(Usuario.nome).all()
	
	return {
		'usuarios': [
			{
				'id': u.id,
				'nome': u.nome,
				'tipo': u.tipo,
				'setor_nome': u.setor.nome if u.setor else 'N/A'
			}
			for u in usuarios
		]
	}


@bp.get('/api/debug')
def api_debug():
	"""Endpoint para debug - verificar dados no banco"""
	try:
		empresas_count = Empresa.query.count()
		tarefas_count = Tarefa.query.count()
		empresas_ativas = Empresa.query.filter_by(ativo=True).count()
		
		# Buscar algumas empresas e tarefas para teste
		empresas_sample = Empresa.query.filter_by(ativo=True).limit(3).all()
		tarefas_sample = Tarefa.query.limit(3).all()
		
		return {
			'empresas_total': empresas_count,
			'empresas_ativas': empresas_ativas,
			'tarefas_total': tarefas_count,
			'empresas_sample': [
				{
					'id': e.id,
					'nome': e.nome,
					'codigo': e.codigo,
					'ativo': e.ativo,
					'tributacao_id': e.tributacao_id
				}
				for e in empresas_sample
			],
			'tarefas_sample': [
				{
					'id': t.id,
					'nome': t.nome,
					'tipo': t.tipo,
					'setor_id': t.setor_id,
					'tributacao_id': t.tributacao_id
				}
				for t in tarefas_sample
			]
		}
	except Exception as e:
		return {'error': str(e)}



