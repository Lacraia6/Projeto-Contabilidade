"""
Testes para models
"""

import pytest
from datetime import datetime
from app.models import Usuario, Setor, Empresa, Tarefa, Tributacao


class TestUsuario:
    """Testes para model Usuario"""
    
    def test_usuario_creation(self, app):
        """Testa criação de usuário"""
        with app.app_context():
            usuario = Usuario.query.filter_by(login='admin').first()
            assert usuario is not None
            assert usuario.nome == 'Admin Test'
            assert usuario.login == 'admin'
            assert usuario.tipo == 'admin'
            assert usuario.ativo == True
    
    def test_usuario_relationships(self, app):
        """Testa relacionamentos do usuário"""
        with app.app_context():
            usuario = Usuario.query.filter_by(login='gerente').first()
            assert usuario.setor is not None
            assert usuario.setor.nome == 'Fiscal'


class TestEmpresa:
    """Testes para model Empresa"""
    
    def test_empresa_creation(self, app):
        """Testa criação de empresa"""
        with app.app_context():
            empresa = Empresa.query.filter_by(codigo='ETA').first()
            assert empresa is not None
            assert empresa.nome == 'Empresa Test A'
            assert empresa.codigo == 'ETA'
            assert empresa.ativo == True
    
    def test_empresa_relationships(self, app):
        """Testa relacionamentos da empresa"""
        with app.app_context():
            empresa = Empresa.query.filter_by(codigo='ETA').first()
            assert empresa.tributacao is not None
            assert empresa.tributacao.nome == 'Simples Nacional'


class TestTarefa:
    """Testes para model Tarefa"""
    
    def test_tarefa_creation(self, app):
        """Testa criação de tarefa"""
        with app.app_context():
            tarefa = Tarefa.query.filter_by(nome='Declaração Mensal').first()
            assert tarefa is not None
            assert tarefa.tipo == 'Mensal'
            assert tarefa.descricao == 'Declaração mensal de impostos'
            assert tarefa.ativo == True
    
    def test_tarefa_relationships(self, app):
        """Testa relacionamentos da tarefa"""
        with app.app_context():
            tarefa = Tarefa.query.filter_by(nome='Declaração Mensal').first()
            assert tarefa.setor is not None
            assert tarefa.setor.nome == 'Fiscal'


class TestSetor:
    """Testes para model Setor"""
    
    def test_setor_creation(self, app):
        """Testa criação de setor"""
        with app.app_context():
            setor = Setor.query.filter_by(nome='Fiscal').first()
            assert setor is not None
            assert setor.nome == 'Fiscal'


class TestTributacao:
    """Testes para model Tributacao"""
    
    def test_tributacao_creation(self, app):
        """Testa criação de tributação"""
        with app.app_context():
            tributacao = Tributacao.query.filter_by(nome='Simples Nacional').first()
            assert tributacao is not None
            assert tributacao.nome == 'Simples Nacional'

