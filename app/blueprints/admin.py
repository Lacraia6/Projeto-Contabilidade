from flask import Blueprint, render_template, request, redirect, url_for, flash, session, send_file
from app.db import db
from app.models import Usuario, Setor, Empresa, Tributacao, Tarefa
import pandas as pd
import io

bp = Blueprint('admin', __name__, url_prefix='/admin')


def require_admin():
	if session.get('user_tipo') != 'admin':
		return redirect(url_for('dashboard.return_dashboard'))
	return None


@bp.get('')
@bp.get('/')

def admin_page():
	guard = require_admin()
	if guard:
		return guard
	setores = Setor.query.all()
	tributacoes = Tributacao.query.all()
	usuarios = Usuario.query.order_by(Usuario.nome).all()
	empresas = Empresa.query.order_by(Empresa.nome).all()
	return render_template('admin.html', aba='admin', setores=setores, tributacoes=tributacoes, usuarios=usuarios, empresas=empresas)


@bp.post('/usuarios')

def create_user():
	guard = require_admin()
	if guard:
		return guard
	u = Usuario(
		nome=request.form.get('nome'),
		login=request.form.get('login'),
		senha=request.form.get('senha'),
		tipo=request.form.get('tipo'),
		setor_id=request.form.get('setor_id', type=int),
		ativo=True
	)
	db.session.add(u)
	db.session.commit()
	flash('Usuário cadastrado!')
	return redirect(url_for('admin.admin_page'))


@bp.post('/empresas')

def create_company():
	guard = require_admin()
	if guard:
		return guard
	e = Empresa(
		codigo=request.form.get('codigo'),
		nome=request.form.get('nome'),
		tributacao_id=request.form.get('tributacao_id', type=int),
		ativo=True
	)
	db.session.add(e)
	db.session.commit()
	flash('Empresa cadastrada!')
	return redirect(url_for('admin.admin_page'))


@bp.post('/usuarios/<int:user_id>/toggle')

def toggle_user(user_id: int):
	guard = require_admin()
	if guard:
		return guard
	u = Usuario.query.get(user_id)
	if not u:
		flash('Usuário não encontrado')
		return redirect(url_for('admin.admin_page'))
	u.ativo = not bool(u.ativo)
	db.session.commit()
	flash('Usuário ativado' if u.ativo else 'Usuário desativado')
	return redirect(url_for('admin.admin_page'))


@bp.post('/empresas/<int:empresa_id>/toggle')

def toggle_company(empresa_id: int):
	guard = require_admin()
	if guard:
		return guard
	e = Empresa.query.get(empresa_id)
	if not e:
		flash('Empresa não encontrada')
		return redirect(url_for('admin.admin_page'))
	e.ativo = not bool(e.ativo)
	db.session.commit()
	flash('Empresa ativada' if e.ativo else 'Empresa desativada')
	return redirect(url_for('admin.admin_page'))


# =====================
# Importação via Excel
# =====================

@bp.post('/import/usuarios')

def import_usuarios():
	guard = require_admin()
	if guard:
		return guard
	file = request.files.get('arquivo')
	if not file:
		flash('Selecione um arquivo de usuários (.xlsx)')
		return redirect(url_for('admin.admin_page'))
	df = pd.read_excel(file)
	# Espera colunas: nome, login, senha, tipo, setor (nome do setor)
	for _, row in df.iterrows():
		setor = None
		if pd.notna(row.get('setor')):
			setor = Setor.query.filter_by(nome=str(row.get('setor')).strip()).first()
			if not setor:
				setor = Setor(nome=str(row.get('setor')).strip())
				db.session.add(setor)
				db.session.flush()
		u = Usuario(
			nome=str(row.get('nome')).strip(),
			login=str(row.get('login')).strip(),
			senha=str(row.get('senha')).strip(),
			tipo=str(row.get('tipo')).strip().lower(),
			setor_id=(setor.id if setor else None),
			ativo=True
		)
		db.session.add(u)
	db.session.commit()
	flash('Importação de usuários concluída!')
	return redirect(url_for('admin.admin_page'))


@bp.post('/import/empresas')

def import_empresas():
	guard = require_admin()
	if guard:
		return guard
	file = request.files.get('arquivo')
	if not file:
		flash('Selecione um arquivo de empresas (.xlsx)')
		return redirect(url_for('admin.admin_page'))
	df = pd.read_excel(file)
	# Espera colunas: codigo, nome, tributacao (nome da tributacao)
	for _, row in df.iterrows():
		trib = None
		if pd.notna(row.get('tributacao')):
			trib = Tributacao.query.filter_by(nome=str(row.get('tributacao')).strip()).first()
			if not trib:
				trib = Tributacao(nome=str(row.get('tributacao')).strip())
				db.session.add(trib)
				db.session.flush()
		e = Empresa(
			codigo=str(row.get('codigo')).strip(),
			nome=str(row.get('nome')).strip(),
			tributacao_id=(trib.id if trib else None),
			ativo=True
		)
		db.session.add(e)
	db.session.commit()
	flash('Importação de empresas concluída!')
	return redirect(url_for('admin.admin_page'))


@bp.post('/import/tarefas')

def import_tarefas():
	guard = require_admin()
	if guard:
		return guard
	file = request.files.get('arquivo')
	if not file:
		flash('Selecione um arquivo de tarefas (.xlsx)')
		return redirect(url_for('admin.admin_page'))
	df = pd.read_excel(file)
	# Espera colunas: nome, tipo, descricao, tributacao (nome), setor (nome)
	for _, row in df.iterrows():
		setor = None
		if pd.notna(row.get('setor')):
			setor = Setor.query.filter_by(nome=str(row.get('setor')).strip()).first()
			if not setor:
				setor = Setor(nome=str(row.get('setor')).strip())
				db.session.add(setor)
				db.session.flush()
		trib = None
		if pd.notna(row.get('tributacao')):
			trib = Tributacao.query.filter_by(nome=str(row.get('tributacao')).strip()).first()
			if not trib:
				trib = Tributacao(nome=str(row.get('tributacao')).strip())
				db.session.add(trib)
				db.session.flush()
		t = Tarefa(
			nome=str(row.get('nome')).strip(),
			tipo=str(row.get('tipo')).strip(),
			descricao=(str(row.get('descricao')).strip() if pd.notna(row.get('descricao')) else None),
			tributacao_id=(trib.id if trib else None),
			setor_id=(setor.id if setor else None)
		)
		db.session.add(t)
	db.session.commit()
	flash('Importação de tarefas concluída!')
	return redirect(url_for('admin.admin_page'))


@bp.post('/change-password')
def change_password():
	"""Altera a senha de um usuário"""
	guard = require_admin()
	if guard:
		return guard
	
	user_id = request.form.get('user_id', type=int)
	new_password = request.form.get('new_password')
	confirm_password = request.form.get('confirm_password')
	
	if not user_id or not new_password or not confirm_password:
		flash('Todos os campos são obrigatórios!')
		return redirect(url_for('admin.admin_page'))
	
	if new_password != confirm_password:
		flash('As senhas não coincidem!')
		return redirect(url_for('admin.admin_page'))
	
	if len(new_password) < 6:
		flash('A senha deve ter pelo menos 6 caracteres!')
		return redirect(url_for('admin.admin_page'))
	
	usuario = Usuario.query.get(user_id)
	if not usuario:
		flash('Usuário não encontrado!')
		return redirect(url_for('admin.admin_page'))
	
	# Atualizar senha
	usuario.senha = new_password
	db.session.commit()
	
	flash(f'Senha alterada com sucesso para o usuário {usuario.nome}!')
	return redirect(url_for('admin.admin_page'))


@bp.post('/change-tributacao')
def change_tributacao():
	"""Altera a tributação de uma empresa"""
	guard = require_admin()
	if guard:
		return guard
	
	empresa_id = request.form.get('empresa_id', type=int)
	nova_tributacao_id = request.form.get('nova_tributacao_id', type=int)
	confirmar_alteracao = request.form.get('confirmar_alteracao')
	
	if not empresa_id or not nova_tributacao_id:
		flash('Todos os campos são obrigatórios!')
		return redirect(url_for('admin.admin_page'))
	
	if not confirmar_alteracao:
		flash('É necessário confirmar que entende sobre a necessidade de refazer os responsáveis pelas tarefas!')
		return redirect(url_for('admin.admin_page'))
	
	empresa = Empresa.query.get(empresa_id)
	if not empresa:
		flash('Empresa não encontrada!')
		return redirect(url_for('admin.admin_page'))
	
	tributacao = Tributacao.query.get(nova_tributacao_id)
	if not tributacao:
		flash('Tributação não encontrada!')
		return redirect(url_for('admin.admin_page'))
	
	# Verificar se a tributação é diferente da atual
	if empresa.tributacao_id == nova_tributacao_id:
		flash('A empresa já possui esta tributação!')
		return redirect(url_for('admin.admin_page'))
	
	# Armazenar tributação anterior para mensagem
	tributacao_anterior = Tributacao.query.get(empresa.tributacao_id)
	tributacao_anterior_nome = tributacao_anterior.nome if tributacao_anterior else 'N/A'
	
	# Atualizar tributação
	empresa.tributacao_id = nova_tributacao_id
	db.session.commit()
	
	flash(f'Tributação alterada com sucesso para a empresa {empresa.nome}! De {tributacao_anterior_nome} para {tributacao.nome}. Lembre-se de refazer os responsáveis pelas tarefas.')
	return redirect(url_for('admin.admin_page'))


@bp.get('/download-template/<tipo>')
def download_template(tipo):
	"""Download de template Excel para importação"""
	guard = require_admin()
	if guard:
		return guard
	
	if tipo == 'usuarios':
		# Template para usuários
		data = {
			'nome': ['João Silva', 'Maria Santos'],
			'login': ['joao.silva', 'maria.santos'],
			'senha': ['123456', '123456'],
			'tipo': ['normal', 'gerente'],
			'setor': ['Departamento Fiscal', 'Departamento Pessoal']
		}
		filename = 'template_usuarios.xlsx'
		
	elif tipo == 'empresas':
		# Template para empresas
		data = {
			'codigo': ['001', '002'],
			'nome': ['Empresa Exemplo 1', 'Empresa Exemplo 2'],
			'tributacao': ['Simples Nacional', 'Regime Normal']
		}
		filename = 'template_empresas.xlsx'
		
	elif tipo == 'tarefas':
		# Template para tarefas
		data = {
			'nome': ['Declaração de Imposto', 'Folha de Pagamento'],
			'tipo': ['mensal', 'mensal'],
			'descricao': ['Declaração mensal de impostos', 'Processamento da folha de pagamento'],
			'tributacao': ['Simples Nacional', 'Regime Normal'],
			'setor': ['Departamento Fiscal', 'Departamento Pessoal']
		}
		filename = 'template_tarefas.xlsx'
		
	else:
		flash('Tipo de template inválido!')
		return redirect(url_for('admin.admin_page'))
	
	# Criar DataFrame
	df = pd.DataFrame(data)
	
	# Criar arquivo em memória
	output = io.BytesIO()
	with pd.ExcelWriter(output, engine='openpyxl') as writer:
		df.to_excel(writer, sheet_name='Template', index=False)
	
	output.seek(0)
	
	return send_file(
		output,
		as_attachment=True,
		download_name=filename,
		mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
	)
