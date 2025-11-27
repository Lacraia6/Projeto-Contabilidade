from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.models import Usuario
from datetime import datetime

bp = Blueprint('auth', __name__, url_prefix='')


@bp.get('/login')

def login_page():
	if session.get('user_id'):
		# Redirecionamento baseado no tipo de usuário já logado
		user_tipo = session.get('user_tipo')
		if user_tipo == 'admin':
			return redirect(url_for('admin.admin_page'))
		elif user_tipo == 'gerente':
			return redirect(url_for('gerenciamento.return_page'))
		elif user_tipo == 'supervisor':
			return redirect(url_for('supervisor.index'))
		else:  # tipo 'normal'
			return redirect(url_for('dashboard.return_dashboard'))
	return render_template('login.html')


@bp.post('/login')

def login_submit():
	login = request.form.get('login', '').strip()
	senha = request.form.get('senha', '').strip()
	user = Usuario.query.filter_by(login=login, senha=senha).first()
	# user = {"user_id": 1, "user_name": "gabriel", "user_tipo": "admin"}
	if not user:
		flash('Usuário ou Senha inválidos')
		return redirect(url_for('auth.login_page'))
	session['user_id'] = user.id
	session['user_nome'] = user.nome
	session['user_tipo'] = user.tipo
	
	# Verificar se é o primeiro login do dia e criar tarefas do período atual se necessário
	# Usar uma flag na sessão para garantir que isso só aconteça uma vez por dia
	hoje_str = datetime.now().strftime('%Y-%m-%d')
	ultima_verificacao = session.get('ultima_verificacao_tarefas', '')
	
	if ultima_verificacao != hoje_str:
		try:
			from app.blueprints.tarefas_auto import verificar_e_criar_tarefas_periodo_atual
			tarefas_criadas, tarefas_existentes, periodo_label = verificar_e_criar_tarefas_periodo_atual()
			
			# Marcar que já verificamos hoje
			session['ultima_verificacao_tarefas'] = hoje_str
			
			# Log silencioso (não mostrar para o usuário, apenas criar as tarefas)
			if tarefas_criadas > 0:
				print(f"✅ Tarefas do período {periodo_label} criadas automaticamente: {tarefas_criadas} novas, {tarefas_existentes} já existentes")
		except Exception as e:
			# Em caso de erro, não bloquear o login, apenas logar o erro
			print(f"⚠️ Erro ao verificar/criar tarefas do período atual no login: {str(e)}")
	
	# Redirecionamento baseado no tipo de usuário
	if user.tipo == 'admin':
		return redirect(url_for('admin.admin_page'))
	elif user.tipo == 'gerente':
		return redirect(url_for('gerenciamento.return_page'))
	elif user.tipo == 'supervisor':
		return redirect(url_for('supervisor.index'))
	else:  # tipo 'normal'
		return redirect(url_for('dashboard.return_dashboard'))


@bp.get('/logout')

def logout():
	session.clear()
	return redirect(url_for('auth.login_page'))
