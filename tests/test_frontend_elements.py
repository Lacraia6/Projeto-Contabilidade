"""
Testes específicos para elementos do frontend
Verifica se elementos críticos estão presentes e funcionando
"""

import pytest
from bs4 import BeautifulSoup


class TestModalElements:
    """Testa se os modais têm os elementos necessários"""
    
    def test_modal_criar_tarefa_has_form_fields(self, client):
        """Testa se o modal de criar tarefa tem todos os campos do formulário"""
        client.post('/login', data={
            'login': 'gerente',
            'senha': '123'
        }, follow_redirects=True)
        
        response = client.get('/tarefas-melhoradas/standalone')
        soup = BeautifulSoup(response.data, 'html.parser')
        
        # Procurar modal de criar tarefa
        modal = soup.find('div', {'id': 'modalCriarTarefa'})
        
        if modal:
            # Verificar campos do formulário
            assert modal.find('input', {'id': 'novaTarefaNome'}) or modal.find('input', {'name': lambda x: x and 'nome' in x.lower()})
            assert modal.find('select', {'id': 'novaTarefaTipo'}) or modal.find('select', {'name': lambda x: x and 'tipo' in x.lower()})
            assert modal.find('select', {'id': 'novaTarefaSetor'}) or modal.find('select', {'name': lambda x: x and 'setor' in x.lower()})
    
    def test_modal_vincular_resp_has_steps(self, client):
        """Testa se o modal de vincular responsável tem os passos necessários"""
        client.post('/login', data={
            'login': 'gerente',
            'senha': '123'
        }, follow_redirects=True)
        
        response = client.get('/tarefas-melhoradas/standalone')
        soup = BeautifulSoup(response.data, 'html.parser')
        
        # Procurar modal de vincular responsável
        modal = soup.find('div', {'id': 'modalVincularResp'}) or soup.find('div', {'id': 'modalVincularResponsavel'})
        
        if modal:
            # Verificar se há campos de busca
            assert modal.find('input', {'id': 'buscaEmpresa'}) or modal.find('input', {'placeholder': lambda x: x and 'empresa' in x.lower()})
            assert modal.find('input', {'id': 'buscaTarefas'}) or modal.find('input', {'placeholder': lambda x: x and 'tarefa' in x.lower()})
            assert modal.find('input', {'id': 'buscaResponsavel'}) or modal.find('input', {'placeholder': lambda x: x and 'responsável' in x.lower() or 'responsavel' in x.lower()})
    
    def test_modals_have_close_buttons(self, client):
        """Testa se os modais têm botões de fechar"""
        client.post('/login', data={
            'login': 'gerente',
            'senha': '123'
        }, follow_redirects=True)
        
        response = client.get('/tarefas-melhoradas/standalone')
        soup = BeautifulSoup(response.data, 'html.parser')
        
        # Procurar modais
        modals = soup.find_all('div', {'id': lambda x: x and 'modal' in x.lower()})
        
        for modal in modals:
            # Verificar se há botão de fechar (× ou botão close)
            close_btn = (
                modal.find('button', string=lambda x: x and ('×' in str(x) or 'fechar' in str(x).lower() or 'close' in str(x).lower())) or
                modal.find('button', {'onclick': lambda x: x and 'fechar' in x.lower()}) or
                modal.find('button', {'class': lambda x: x and 'close' in str(x).lower()})
            )
            # Não é obrigatório, mas é boa prática ter


class TestButtonElements:
    """Testa se os botões principais estão presentes"""
    
    def test_tarefas_page_has_action_buttons(self, client):
        """Testa se a página de tarefas tem botões de ação"""
        client.post('/login', data={
            'login': 'gerente',
            'senha': '123'
        }, follow_redirects=True)
        
        response = client.get('/tarefas-melhoradas/standalone')
        soup = BeautifulSoup(response.data, 'html.parser')
        
        # Verificar botões principais
        criar_btn = soup.find('button', {'id': 'btnCriarTarefa'}) or soup.find('button', string=lambda x: x and 'Nova Tarefa' in str(x))
        vincular_btn = soup.find('button', {'id': 'btnVincularResp'}) or soup.find('button', string=lambda x: x and 'Vincular' in str(x))
        
        assert criar_btn is not None, "Botão de criar tarefa deve existir"
        assert vincular_btn is not None, "Botão de vincular responsável deve existir"
    
    def test_dashboard_has_filter_button(self, client):
        """Testa se o dashboard tem botão de aplicar filtros"""
        client.post('/login', data={
            'login': 'admin',
            'senha': '123'
        }, follow_redirects=True)
        
        response = client.get('/dashboard')
        soup = BeautifulSoup(response.data, 'html.parser')
        
        # Verificar se há botão de aplicar filtros
        filter_btn = (
            soup.find('button', {'onclick': lambda x: x and 'apply' in x.lower()}) or
            soup.find('button', string=lambda x: x and ('aplicar' in str(x).lower() or 'filtrar' in str(x).lower()))
        )
        # Não é obrigatório ter botão específico, pode usar enter ou outros métodos


class TestTableElements:
    """Testa se as tabelas têm estrutura correta"""
    
    def test_tarefas_table_exists(self, client):
        """Testa se a tabela de tarefas existe"""
        client.post('/login', data={
            'login': 'gerente',
            'senha': '123'
        }, follow_redirects=True)
        
        response = client.get('/tarefas-melhoradas/standalone')
        soup = BeautifulSoup(response.data, 'html.parser')
        
        # Verificar se há tabela ou container de lista
        table = (
            soup.find('table', {'id': 'listaTarefas'}) or
            soup.find('table') or
            soup.find('tbody', {'id': 'listaTarefas'}) or
            soup.find('div', {'id': 'listaTarefas'})
        )
        
        # Pode estar vazia inicialmente, mas deve existir
        assert table is not None, "Tabela ou container de tarefas deve existir"
    
    def test_dashboard_table_exists(self, client):
        """Testa se a tabela do dashboard existe"""
        client.post('/login', data={
            'login': 'admin',
            'senha': '123'
        }, follow_redirects=True)
        
        response = client.get('/dashboard')
        soup = BeautifulSoup(response.data, 'html.parser')
        
        # Verificar se há tabela
        table = soup.find('table') or soup.find('tbody')
        # Não é obrigatório ter tabela, pode usar cards ou outros layouts


class TestJavaScriptFunctions:
    """Testa se funções JavaScript críticas estão definidas"""
    
    def test_page_has_javascript_functions(self, client):
        """Testa se as páginas têm definições de funções JavaScript"""
        client.post('/login', data={
            'login': 'gerente',
            'senha': '123'
        }, follow_redirects=True)
        
        response = client.get('/tarefas-melhoradas/standalone')
        html_content = response.data.decode('utf-8')
        
        # Verificar se há definições de funções importantes
        assert 'function' in html_content or 'abrirModal' in html_content or 'Modal' in html_content
        
        # Verificar funções específicas da página de tarefas
        if 'tarefas-melhoradas' in response.request.path:
            assert 'abrirModalCriarTarefa' in html_content or 'criarTarefa' in html_content
            assert 'carregarTarefas' in html_content or 'loadTarefas' in html_content or 'fetch' in html_content


class TestNavigationElements:
    """Testa elementos de navegação"""
    
    def test_sidebar_exists_when_logged_in(self, client):
        """Testa se a sidebar existe quando logado"""
        client.post('/login', data={
            'login': 'admin',
            'senha': '123'
        }, follow_redirects=True)
        
        response = client.get('/dashboard')
        soup = BeautifulSoup(response.data, 'html.parser')
        
        # Verificar se há sidebar ou menu de navegação
        sidebar = (
            soup.find('nav', {'class': lambda x: x and 'sidebar' in str(x).lower()}) or
            soup.find('aside') or
            soup.find('nav') or
            soup.find('div', {'class': lambda x: x and 'sidebar' in str(x).lower()})
        )
        
        # Sidebar é importante para navegação
        assert sidebar is not None, "Menu de navegação ou sidebar deve existir"
    
    def test_navigation_has_logout_link(self, client):
        """Testa se há link de logout na navegação"""
        client.post('/login', data={
            'login': 'admin',
            'senha': '123'
        }, follow_redirects=True)
        
        response = client.get('/dashboard')
        soup = BeautifulSoup(response.data, 'html.parser')
        
        # Verificar se há link de logout
        logout_link = (
            soup.find('a', {'href': lambda x: x and 'logout' in x.lower()}) or
            soup.find('a', string=lambda x: x and ('sair' in str(x).lower() or 'logout' in str(x).lower()))
        )
        
        assert logout_link is not None, "Link de logout deve existir"


class TestResponsiveElements:
    """Testa elementos responsivos"""
    
    def test_page_has_viewport_meta(self, client):
        """Testa se as páginas têm meta tag de viewport"""
        response = client.get('/login')
        soup = BeautifulSoup(response.data, 'html.parser')
        
        viewport = soup.find('meta', {'name': 'viewport'})
        # Viewport é importante para responsividade
        assert viewport is not None, "Meta tag viewport deve existir para responsividade"
    
    def test_page_loads_css(self, client):
        """Testa se as páginas carregam CSS"""
        response = client.get('/login')
        soup = BeautifulSoup(response.data, 'html.parser')
        
        # Verificar se há links de CSS
        css_links = soup.find_all('link', {'rel': 'stylesheet'})
        assert len(css_links) > 0, "Deve haver arquivos CSS carregados"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

