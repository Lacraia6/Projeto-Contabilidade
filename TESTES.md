# 🧪 Guia de Testes

## Visão Geral

Este projeto utiliza **pytest** para testes automatizados, garantindo qualidade e confiabilidade do código.

## Instalação

### 1. Instalar dependências de teste

```bash
pip install -r requirements.txt
```

Isso instalará:
- `pytest` - Framework de testes
- `pytest-cov` - Cobertura de código
- `pytest-flask` - Suporte para Flask

## Executando os Testes

### Executar todos os testes

```bash
pytest
```

### Executar com cobertura de código

```bash
pytest --cov=app --cov-report=html
```

Isso gera um relatório HTML em `htmlcov/index.html`.

### Executar um arquivo específico

```bash
pytest tests/test_utils.py
```

### Executar uma classe específica

```bash
pytest tests/test_utils.py::TestPeriodUtils
```

### Executar um teste específico

```bash
pytest tests/test_utils.py::TestPeriodUtils::test_get_previous_period
```

## Estrutura de Testes

```
tests/
├── __init__.py           # Inicialização do módulo de testes
├── conftest.py          # Configuração global e fixtures
├── test_auth.py         # Testes de autenticação
├── test_utils.py        # Testes de funções utilitárias
├── test_models.py       # Testes de models
└── test_api.py          # Testes de APIs
```

## Fixtures Disponíveis

### `app`
Cria uma instância da aplicação para testes com:
- Banco de dados em memória (SQLite)
- Autenticação desabilitada
- Dados de teste pré-configurados

### `client`
Cria um cliente de teste para fazer requisições HTTP

### `runner`
Cria um runner CLI para testar comandos linha de comando

## Dados de Teste

Os dados de teste são automaticamente criados no `conftest.py`:

- **Setores**: Fiscal, Contábil
- **Tributação**: Simples Nacional, Regime Normal
- **Usuários**: 
  - Admin (admin/123)
  - Gerente (gerente/123)
  - Colaborador (colaborador/123)
- **Empresas**: Empresa Test A, Empresa Test B
- **Tarefas**: Declaração Mensal, SPED Contábil

## Exemplos de Testes

### Teste de Função Utilitária

```python
def test_get_previous_period():
    """Testa geração de período anterior"""
    periodo = get_previous_period()
    assert '/' in periodo
    parts = periodo.split('/')
    assert len(parts) == 2
```

### Teste de API

```python
def test_api_empresas_list(client):
    """Testa listagem de empresas via API"""
    response = client.get('/api/empresas')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'empresas' in data
```

### Teste de Model

```python
def test_usuario_creation(app):
    """Testa criação de usuário"""
    with app.app_context():
        usuario = Usuario.query.filter_by(login='admin').first()
        assert usuario is not None
        assert usuario.nome == 'Admin Test'
```

## Marcadores

Os testes podem ser marcados para execução seletiva:

### Marcar um teste

```python
@pytest.mark.slow
def test_complex_operation():
    # Teste que demora muito
    pass
```

### Executar apenas testes unitários

```bash
pytest -m unit
```

### Executar apenas testes rápidos

```bash
pytest -m "not slow"
```

## Cobertura de Código

### Verificar cobertura atual

```bash
pytest --cov=app --cov-report=term-missing
```

### Gerar relatório HTML

```bash
pytest --cov=app --cov-report=html
open htmlcov/index.html  # Linux/Mac
start htmlcov/index.html  # Windows
```

### Meta de Cobertura

- **Mínimo**: 70% de cobertura geral
- **Ideal**: 85%+ de cobertura geral
- **Funções críticas**: 100% de cobertura

## Boas Práticas

### 1. Nomenclatura Clara

```python
def test_login_with_valid_credentials():  # ✅ Bom
def test_auth():  # ❌ Vago
```

### 2. Um Asserção por Comportamento

```python
def test_period_format():
    periodo = get_previous_period()
    assert '/' in periodo  # Formato
    parts = periodo.split('/')
    assert len(parts) == 2  # Estrutura
```

### 3. Usar Fixtures

```python
def test_empresa_access(client):  # ✅ Usa fixture
    response = client.get('/api/empresas')
    assert response.status_code == 200
```

### 4. Testes Independentes

Cada teste deve poder executar independentemente, sem depender de outros testes.

### 5. Arrange-Act-Assert

```python
def test_login_success(client):
    # Arrange: Preparar dados
    login_data = {'login': 'admin', 'senha': '123'}
    
    # Act: Executar ação
    response = client.post('/auth/login', data=login_data)
    
    # Assert: Verificar resultado
    assert response.status_code == 200
```

## Integração Contínua

Os testes podem ser executados em CI/CD:

```yaml
# Exemplo para GitHub Actions
- name: Run tests
  run: |
    pip install -r requirements.txt
    pytest --cov=app --cov-report=xml
```

## Troubleshooting

### Testes falhando com autenticação

- Verifique se `AUTH_ENABLED` está desabilitado no app de teste
- Use `client` fixture que gerencia sessão automaticamente

### Problemas com banco de dados

- Os testes usam banco em memória (SQLite)
- Dados são resetados entre execuções
- Não interfere com banco de desenvolvimento/produção

### Import errors

- Certifique-se de executar `pytest` da raiz do projeto
- Verifique que `app` está no PYTHONPATH

## Próximos Passos

- [ ] Adicionar testes de integração
- [ ] Implementar testes end-to-end
- [ ] Adicionar testes de performance
- [ ] Configurar CI/CD com GitHub Actions
- [ ] Adicionar testes de carga (locust)

## Referências

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-flask Documentation](https://pytest-flask.readthedocs.io/)
- [Testing Best Practices](https://docs.python-guide.org/writing/tests/)

