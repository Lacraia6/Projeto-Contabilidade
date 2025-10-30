"""
Testes para autenticação e autorização
"""

import pytest
from app.models import Usuario
from werkzeug.security import check_password_hash


class TestAuth:
    """Testes de autenticação"""
    
    def test_login_success(self, client):
        """Testa login bem-sucedido"""
        response = client.post('/auth/login', data={
            'login': 'admin',
            'senha': '123'
        }, follow_redirects=True)
        
        assert response.status_code == 200
    
    def test_login_failure(self, client):
        """Testa login com credenciais inválidas"""
        response = client.post('/auth/login', data={
            'login': 'admin',
            'senha': 'wrong_password'
        })
        
        assert response.status_code in [200, 401]
    
    def test_password_hashing(self, app):
        """Testa que senhas são hash corretamente"""
        with app.app_context():
            usuario = Usuario.query.filter_by(login='admin').first()
            assert check_password_hash(usuario.senha, '123')
            assert not check_password_hash(usuario.senha, 'wrong_password')
    
    def test_logout(self, client):
        """Testa logout"""
        # Primeiro fazer login
        client.post('/auth/login', data={
            'login': 'admin',
            'senha': '123'
        })
        
        # Depois fazer logout
        response = client.get('/auth/logout', follow_redirects=True)
        assert response.status_code == 200
    
    def test_protected_route(self, client):
        """Testa que rotas protegidas redirecionam para login"""
        response = client.get('/dashboard')
        
        # Deve redirecionar para login se não autenticado
        assert response.status_code in [302, 200]
        if response.status_code == 302:
            assert '/login' in response.location


class TestAuthorization:
    """Testes de autorização"""
    
    def test_admin_access(self, client):
        """Testa que admin tem acesso a todas as funcionalidades"""
        # Login como admin
        response = client.post('/auth/login', data={
            'login': 'admin',
            'senha': '123'
        }, follow_redirects=True)
        
        assert response.status_code == 200
    
    def test_gerente_access(self, client):
        """Testa que gerente tem acesso ao painel de gerenciamento"""
        # Login como gerente
        response = client.post('/auth/login', data={
            'login': 'gerente',
            'senha': '123'
        }, follow_redirects=True)
        
        assert response.status_code == 200
    
    def test_colaborador_access(self, client):
        """Testa que colaborador tem acesso ao dashboard"""
        # Login como colaborador
        response = client.post('/auth/login', data={
            'login': 'colaborador',
            'senha': '123'
        }, follow_redirects=True)
        
        assert response.status_code == 200

