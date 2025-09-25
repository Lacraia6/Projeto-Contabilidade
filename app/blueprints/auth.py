from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.models import Usuario

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
	
	# Redirecionamento baseado no tipo de usuário
	if user.tipo == 'admin':
		return redirect(url_for('admin.admin_page'))
	elif user.tipo == 'gerente':
		return redirect(url_for('gerenciamento.return_page'))
	else:  # tipo 'normal'
		return redirect(url_for('dashboard.return_dashboard'))


@bp.get('/logout')

def logout():
	session.clear()
	return redirect(url_for('auth.login_page'))
