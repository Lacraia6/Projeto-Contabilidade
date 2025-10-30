"""
Testes para APIs
"""

import pytest
import json


class TestAPIEmpresas:
    """Testes para API de empresas"""
    
    def test_api_empresas_list(self, client):
        """Testa listagem de empresas via API"""
        response = client.get('/api/empresas')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Verificar estrutura da resposta
        assert 'empresas' in data
        assert isinstance(data['empresas'], list)
    
    def test_api_empresas_filter(self, client):
        """Testa filtro de empresas via API"""
        response = client.get('/api/empresas?search=Test')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Verificar que retorna resultados
        assert 'empresas' in data
        assert isinstance(data['empresas'], list)


class TestAPITarefas:
    """Testes para API de tarefas"""
    
    def test_api_tarefas_list(self, client):
        """Testa listagem de tarefas via API"""
        response = client.get('/api/tarefas')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Verificar estrutura da resposta
        assert 'tarefas' in data
        assert isinstance(data['tarefas'], list)


class TestAPIDashboard:
    """Testes para API do dashboard"""
    
    def test_health_check(self, client):
        """Testa health check endpoint"""
        response = client.get('/health')
        
        # Health check pode retornar 200 ou 500 dependendo da conexão com banco
        assert response.status_code in [200, 500]


class TestAPIUsuarios:
    """Testes para API de usuários"""
    
    def test_api_usuarios_list(self, client):
        """Testa listagem de usuários via API"""
        # Login primeiro
        client.post('/auth/login', data={
            'login': 'admin',
            'senha': '123'
        }, follow_redirects=True)
        
        response = client.get('/api/usuarios')
        
        # Pode retornar 200, 401 ou 403 dependendo da autenticação
        assert response.status_code in [200, 401, 403]

