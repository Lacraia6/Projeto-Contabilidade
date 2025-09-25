from flask import Blueprint, render_template
from app.models import Empresa

bp = Blueprint('empresas', __name__, url_prefix='/empresas')


@bp.get('')
@bp.get('/')
def return_page():
	empresas = []
	for e in Empresa.query.order_by(Empresa.nome).all():
		empresas.append({
			"id": e.id,
			"empresa_id": e.id,
			"empresa_nome": e.nome,
			"empresa_cnpj": '—',
			"contas_pendentes": [],
			"periodos": [],
			"filiais": [],
		})
	return render_template('empresas.html', aba='empresas', empresas=empresas)



