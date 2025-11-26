"""
Configuração global para pytest
"""

import os
import pytest
from app import create_app
from app.db import db
from app.models import Usuario, Setor, Empresa, Tarefa, Tributacao
from werkzeug.security import generate_password_hash


@pytest.fixture(scope='session')
def app():
    """Cria uma instância da aplicação para testes"""
    os.environ['APP_ENV'] = 'testing'
    os.environ.setdefault('TEST_DATABASE_URL', 'sqlite:///:memory:')
    app = create_app('testing')
    
    with app.app_context():
        db.create_all()
        
        # Criar dados de teste
        setup_test_data()
        
        yield app
        
        db.drop_all()


@pytest.fixture
def client(app):
    """Cria um cliente de teste"""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Cria um runner CLI de teste"""
    return app.test_cli_runner()


def setup_test_data():
    """Configura dados de teste no banco"""
    # Criar setores
    setor_fiscal = Setor(nome='Fiscal')
    setor_contabil = Setor(nome='Contábil')
    db.session.add(setor_fiscal)
    db.session.add(setor_contabil)
    db.session.flush()
    
    # Criar tributação
    simples = Tributacao(nome='Simples Nacional')
    normal = Tributacao(nome='Regime Normal')
    db.session.add(simples)
    db.session.add(normal)
    db.session.flush()
    
    # Criar usuários
    admin = Usuario(
        nome='Admin Test',
        login='admin',
        senha=generate_password_hash('123'),
        tipo='admin',
        ativo=True
    )
    gerente = Usuario(
        nome='Gerente Test',
        login='gerente',
        senha=generate_password_hash('123'),
        tipo='gerente',
        setor_id=setor_fiscal.id,
        ativo=True
    )
    colaborador = Usuario(
        nome='Colaborador Test',
        login='colaborador',
        senha=generate_password_hash('123'),
        tipo='normal',
        setor_id=setor_fiscal.id,
        ativo=True
    )
    db.session.add_all([admin, gerente, colaborador])
    db.session.flush()
    
    # Criar empresas
    empresa1 = Empresa(
        nome='Empresa Test A',
        codigo='ETA',
        tributacao_id=simples.id,
        ativo=True
    )
    empresa2 = Empresa(
        nome='Empresa Test B',
        codigo='ETB',
        tributacao_id=normal.id,
        ativo=True
    )
    db.session.add_all([empresa1, empresa2])
    db.session.flush()
    
    # Criar tarefas
    tarefa1 = Tarefa(
        nome='Declaração Mensal',
        tipo='Mensal',
        descricao='Declaração mensal de impostos',
        setor_id=setor_fiscal.id
    )
    tarefa2 = Tarefa(
        nome='SPED Contábil',
        tipo='Anual',
        descricao='SPED contábil anual',
        setor_id=setor_contabil.id
    )
    db.session.add_all([tarefa1, tarefa2])
    db.session.flush()
    
    db.session.commit()

