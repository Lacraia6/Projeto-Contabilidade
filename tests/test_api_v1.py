import pytest
from app.db import db
from app.models import Usuario


@pytest.fixture
def admin_user(app):
	with app.app_context():
		return Usuario.query.filter_by(login='admin').first()


def set_session_user(client, user_id):
	with client.session_transaction() as sess:
		sess['user_id'] = user_id


class TestApiV1:
	def test_empresas_list_basic(self, app, client, admin_user):
		set_session_user(client, admin_user.id)
		resp = client.get('/api/v1/empresas')
		assert resp.status_code == 200
		data = resp.get_json()
		assert data['success'] is True
		assert 'data' in data
		assert 'pagination' in data
		assert data['pagination']['total'] >= 2
		assert isinstance(data['data'], list)
		assert data['pagination']['total_pages'] >= 1
		assert {'id', 'nome'} <= set(data['data'][0].keys())

	def test_empresas_filter_q(self, app, client, admin_user):
		set_session_user(client, admin_user.id)
		resp = client.get('/api/v1/empresas?q=Test A')
		assert resp.status_code == 200
		data = resp.get_json()
		names = [e['nome'] for e in data['data']]
		assert any('Test A' in n for n in names)

	def test_tarefas_list_basic(self, app, client, admin_user):
		set_session_user(client, admin_user.id)
		resp = client.get('/api/v1/tarefas')
		assert resp.status_code == 200
		data = resp.get_json()
		assert data['success'] is True
		assert 'data' in data
		assert data['pagination']['total'] >= 2
		assert isinstance(data['data'], list)
		assert {'id', 'nome'} <= set(data['data'][0].keys())

	def test_tarefas_filter_tipo(self, app, client, admin_user):
		set_session_user(client, admin_user.id)
		resp = client.get('/api/v1/tarefas?tipo=Mensal')
		assert resp.status_code == 200
		data = resp.get_json()
		for t in data['data']:
			assert t['tipo'] == 'Mensal'
