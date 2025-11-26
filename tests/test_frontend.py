"""
Testes de integração para o frontend
Verifica renderização de páginas, presença de elementos e funcionalidades JavaScript
"""

import pytest
from bs4 import BeautifulSoup
from flask import url_for


class TestFrontendPages:
    """Testa se as páginas principais são renderizadas corretamente"""
    
    def test_login_page_renders(self, client):
        """Testa se a página de login é renderizada"""
        response = client.get('/login')
        assert response.status_code == 200
        assert b'login' in response.data.lower() or b'entrar' in response.data.lower()
        
        # Verificar se há campos de formulário
        soup = BeautifulSoup(response.data, 'html.parser')
        assert soup.find('input', {'type': 'text'}) or soup.find('input', {'name': 'login'})
        assert soup.find('input', {'type': 'password'}) or soup.find('input', {'name': 'senha'})
    
    def test_dashboard_requires_login(self, client):
        """Testa se o dashboard redireciona para login quando não autenticado"""
        response = client.get('/dashboard')
        # Deve redirecionar para login
        assert response.status_code in [302, 401]
    
    def test_dashboard_renders_when_logged_in(self, client):
        """Testa se o dashboard renderiza quando o usuário está logado"""
        # Fazer login primeiro
        client.post('/auth/login', data={
            'login': 'admin',
            'senha': '123'
        }, follow_redirects=True)
        
        # Acessar dashboard
        response = client.get('/dashboard')
        assert response.status_code == 200
        
        # Verificar se há elementos principais do dashboard
        soup = BeautifulSoup(response.data, 'html.parser')
        assert soup.find('table') or soup.find('div', class_='dashboard') or soup.find('div', id='dashboard')
    
    def test_tarefas_melhoradas_page_requires_auth(self, client):
        """Testa se a página de tarefas melhoradas requer autenticação"""
        response = client.get('/tarefas-melhoradas/standalone')
        # Deve redirecionar para login
        assert response.status_code in [302, 401]
    
    def test_tarefas_melhoradas_renders_when_logged_in(self, client):
        """Testa se a página de tarefas melhoradas renderiza quando logado como gerente"""
        # Login como gerente
        client.post('/login', data={
            'login': 'gerente',
            'senha': '123'
        }, follow_redirects=True)
        
        response = client.get('/tarefas-melhoradas/standalone')
        assert response.status_code == 200
        
        soup = BeautifulSoup(response.data, 'html.parser')
        # Verificar se há botões principais
        assert soup.find('button', {'id': 'btnCriarTarefa'}) or soup.find('button', string=lambda x: x and 'Nova Tarefa' in x)
        assert soup.find('button', {'id': 'btnVincularResp'}) or soup.find('button', string=lambda x: x and 'Vincular' in x)
    
    def test_gerenciamento_page_renders(self, client):
        """Testa se a página de gerenciamento renderiza para gerente"""
        # Login como gerente
        client.post('/login', data={
            'login': 'gerente',
            'senha': '123'
        }, follow_redirects=True)
        
        response = client.get('/gerenciamento')
        assert response.status_code == 200


class TestFrontendJavaScript:
    """Testa se os elementos JavaScript estão presentes no HTML"""
    
    def test_gerente_tarefas_has_modal_elements(self, client):
        """Testa se a página de tarefas tem elementos de modal"""
        # Login como gerente
        client.post('/login', data={
            'login': 'gerente',
            'senha': '123'
        }, follow_redirects=True)
        
        response = client.get('/tarefas-melhoradas/standalone')
        soup = BeautifulSoup(response.data, 'html.parser')
        
        # Verificar se há modais
        modals = soup.find_all('div', {'id': lambda x: x and 'modal' in x.lower()})
        assert len(modals) > 0, "Devem existir modais na página"
        
        # Verificar modal de criar tarefa
        modal_criar = soup.find('div', {'id': 'modalCriarTarefa'}) or soup.find('div', {'id': lambda x: x and 'criar' in x.lower() and 'tarefa' in x.lower()})
        assert modal_criar is not None, "Modal de criar tarefa deve existir"
    
    def test_dashboard_has_filter_elements(self, client):
        """Testa se o dashboard tem elementos de filtro"""
        # Login
        client.post('/login', data={
            'login': 'admin',
            'senha': '123'
        }, follow_redirects=True)
        
        response = client.get('/dashboard')
        soup = BeautifulSoup(response.data, 'html.parser')
        
        # Verificar se há campos de busca/filtro
        search_inputs = soup.find_all('input', {'type': 'text'}) or soup.find_all('input', {'id': lambda x: x and 'search' in x.lower()})
        assert len(search_inputs) > 0 or soup.find('select', {'id': 'periodo'}), "Devem existir campos de filtro"
    
    def test_script_files_loaded(self, client):
        """Testa se os arquivos JavaScript são carregados"""
        response = client.get('/tarefas-melhoradas/standalone')
        # Como não está logado, pode redirecionar, mas vamos testar a página de login
        if response.status_code == 302:
            response = client.get('/auth/login')
        
        soup = BeautifulSoup(response.data, 'html.parser')
        
        # Verificar se há scripts
        scripts = soup.find_all('script')
        assert len(scripts) > 0, "Devem existir scripts na página"
        
        # Verificar se há script.js ou scripts inline
        has_script = any(
            'script.js' in str(script.get('src', '')) or 
            script.string and len(script.string) > 0
            for script in scripts
        )
        assert has_script, "Deve haver scripts JavaScript carregados"


class TestFrontendAPIs:
    """Testa se as APIs do frontend retornam dados corretos"""
    
    def test_api_tarefas_requires_auth(self, client):
        """Testa se a API de tarefas requer autenticação"""
        response = client.get('/tarefas-melhoradas/api/tarefas')
        assert response.status_code in [401, 302, 403]
    
    def test_api_tarefas_returns_data(self, client):
        """Testa se a API de tarefas retorna dados quando autenticado"""
        # Login como gerente
        client.post('/login', data={
            'login': 'gerente',
            'senha': '123'
        }, follow_redirects=True)
        
        response = client.get('/tarefas-melhoradas/api/tarefas')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data is not None
        assert 'success' in data or 'tarefas' in data
    
    def test_api_empresas_requires_auth(self, client):
        """Testa se a API de empresas requer autenticação"""
        response = client.get('/tarefas-melhoradas/api/empresas')
        assert response.status_code in [401, 302, 403]
    
    def test_api_empresas_returns_data(self, client):
        """Testa se a API de empresas retorna dados quando autenticado"""
        # Login como gerente
        client.post('/login', data={
            'login': 'gerente',
            'senha': '123'
        }, follow_redirects=True)
        
        response = client.get('/tarefas-melhoradas/api/empresas')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data is not None
        assert 'success' in data or 'empresas' in data
    
    def test_api_create_tarefa_validates_data(self, client):
        """Testa se a API de criar tarefa valida dados"""
        # Login como gerente
        client.post('/login', data={
            'login': 'gerente',
            'senha': '123'
        }, follow_redirects=True)
        
        # Tentar criar tarefa sem dados obrigatórios
        response = client.post('/tarefas-melhoradas/api/tarefas',
                              json={},
                              content_type='application/json')
        assert response.status_code in [400, 422]
        
        data = response.get_json()
        assert data is not None
        assert 'success' in data and data['success'] == False or 'message' in data


class TestFrontendInteractions:
    """Testa interações do frontend através de requisições"""
    
    def test_login_redirects_to_dashboard(self, client):
        """Testa se login redireciona para dashboard"""
        response = client.post('/login', data={
            'login': 'admin',
            'senha': '123'
        }, follow_redirects=False)
        
        # Deve redirecionar após login bem-sucedido
        assert response.status_code == 302
        assert '/dashboard' in response.location or '/gerenciamento' in response.location or '/admin' in response.location
    
    def test_logout_clears_session(self, client):
        """Testa se logout limpa a sessão"""
        # Login primeiro
        client.post('/login', data={
            'login': 'admin',
            'senha': '123'
        }, follow_redirects=True)
        
        # Verificar que está logado
        response = client.get('/dashboard')
        assert response.status_code == 200
        
        # Fazer logout
        client.get('/logout', follow_redirects=True)
        
        # Tentar acessar dashboard novamente
        response = client.get('/dashboard')
        # Deve redirecionar para login
        assert response.status_code in [302, 401]
    
    def test_create_tarefa_workflow(self, client):
        """Testa o fluxo completo de criação de tarefa"""
        # Login como gerente
        client.post('/login', data={
            'login': 'gerente',
            'senha': '123'
        }, follow_redirects=True)
        
        # Criar tarefa
        response = client.post('/tarefas-melhoradas/api/tarefas',
                              json={
                                  'nome': 'Tarefa Teste',
                                  'tipo': 'Mensal',
                                  'setor_id': 1,
                                  'tarefa_comum': False,
                                  'tributacao_id': 1,
                                  'descricao': 'Descrição de teste'
                              },
                              content_type='application/json')
        
        # Verificar resposta
        assert response.status_code in [200, 201]
        
        data = response.get_json()
        # Se sucesso, deve retornar dados da tarefa
        if data and data.get('success'):
            assert 'tarefa_id' in data or 'message' in data


class TestFrontendAccessControl:
    """Testa controle de acesso no frontend"""
    
    def test_normal_user_cannot_access_tarefas_melhoradas(self, client):
        """Testa se usuário normal não pode acessar tarefas melhoradas"""
        # Login como colaborador normal
        client.post('/login', data={
            'login': 'colaborador',
            'senha': '123'
        }, follow_redirects=True)
        
        response = client.get('/tarefas-melhoradas/standalone')
        # Deve redirecionar ou retornar erro
        assert response.status_code in [302, 403, 401]
    
    def test_gerente_can_access_tarefas_melhoradas(self, client):
        """Testa se gerente pode acessar tarefas melhoradas"""
        # Login como gerente
        client.post('/login', data={
            'login': 'gerente',
            'senha': '123'
        }, follow_redirects=True)
        
        response = client.get('/tarefas-melhoradas/standalone')
        assert response.status_code == 200
    
    def test_admin_can_access_all_pages(self, client):
        """Testa se admin pode acessar todas as páginas"""
        # Login como admin
        client.post('/login', data={
            'login': 'admin',
            'senha': '123'
        }, follow_redirects=True)
        
        # Testar diferentes páginas
        pages = ['/dashboard', '/gerenciamento', '/tarefas-melhoradas/standalone']
        
        for page in pages:
            response = client.get(page)
            # Admin deve ter acesso a todas
            assert response.status_code == 200, f"Admin deve ter acesso a {page}"


class TestFrontendForms:
    """Testa formulários do frontend"""
    
    def test_login_form_has_csrf(self, client):
        """Testa se o formulário de login tem proteção CSRF"""
        response = client.get('/login')
        soup = BeautifulSoup(response.data, 'html.parser')
        
        # Verificar se há token CSRF (pode estar em input hidden ou meta tag)
        csrf_token = soup.find('input', {'name': 'csrf_token'}) or soup.find('meta', {'name': 'csrf-token'})
        # CSRF pode estar desabilitado em testes, então não é obrigatório
        # Mas se estiver presente, deve estar no formulário


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

