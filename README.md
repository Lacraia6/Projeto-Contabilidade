# Projeto Contabilidade

Este projeto utiliza Flask com uma arquitetura modularizada por *blueprints*, camada de serviços e suporte opcional a Redis para cache e rate limiting. Abaixo estão as instruções essenciais para configuração, execução e testes.

## 1. Pré-requisitos
- Python 3.11+
- Pipenv ou virtualenv
- MySQL/MariaDB (produção/desenvolvimento) ou SQLite (testes)
- Redis opcional para cache e rate limiting (recomendado em produção)

## 2. Variáveis de Ambiente
| Variável | Descrição | Exemplo |
|----------|-----------|---------|
| `APP_ENV` | Define o perfil de configuração (`development`, `testing`, `production`). | `development` |
| `DATABASE_URL` | URL padrão do banco para execução. | `mysql+pymysql://user:pass@localhost/contabilidade` |
| `TEST_DATABASE_URL` | URL de banco usada no modo `testing`. | `sqlite:///:memory:` |
| `SECRET_KEY` | Chave secreta Flask. | `minha-chave-aleatoria` |
| `REDIS_URL` | URL para Redis (cache/rate limit). | `redis://localhost:6379/0` |
| `CACHE_DEFAULT_TIMEOUT` | Timeout padrão do cache em segundos. | `300` |
| `HOST` / `PORT` | Host/porta para `run.py` e `wsgi.py`. | `0.0.0.0` / `5600` |
| `AUTO_OPEN_BROWSER` | Controla abertura automática do browser (`1` habilita). | `0` |

> Se `REDIS_URL` não estiver definido, o sistema usa `SimpleCache` em memória no modo padrão e `NullCache` durante os testes.

## 3. Configurações por Ambiente
- **Development** (`APP_ENV=development` – padrão): debug ativo, cache simples.
- **Testing** (`APP_ENV=testing`): desabilita autenticação, usa SQLite em memória, desliga cache e rate limiting.
- **Production** (`APP_ENV=production`): ideal para deploy; defina `DATABASE_URL`, `SECRET_KEY` e `REDIS_URL`.

## 4. Instalação
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate  # Windows
type pip install -r requirements.txt
```

## 5. Execução
- **Servidor de desenvolvimento**
  ```bash
  export APP_ENV=development  # Windows: set APP_ENV=development
  python run.py
  ```
  - Usa host/porta configurados por `HOST`/`PORT` (5600 por padrão).
- **Servidor Waitress (produção/local)**
  ```bash
  export APP_ENV=production
  python wsgi.py
  ```
  - Aplica `ProxyFix`, registra requisições e, se `AUTO_OPEN_BROWSER=1`, abre o navegador automaticamente.

## 6. Testes
```bash
export APP_ENV=testing
pytest -v
```
- Os testes configuram `NullCache` e usam `TEST_DATABASE_URL` (padrão `sqlite:///:memory:`).

## 7. Cache & Rate Limiting
- Com `REDIS_URL` definido:
  - Cache usa `RedisCache` via Flask-Caching.
  - Rate limiting (Flask-Limiter) utiliza o mesmo Redis.
- Sem Redis: cache simples em memória e rate limiting baseado em memória.

## 8. Estrutura Relevante
- `app/config.py`: classes de configuração (`Base/Development/Testing/Production`).
- `app/__init__.py`: factory `create_app` que aplica a configuração conforme `APP_ENV`.
- `run.py` / `wsgi.py`: inicialização baseada nas variáveis de ambiente.

## 9. Próximos Passos Sugeridos
- Consolidar blueprints redundantes em módulos de domínio.
- Aumentar cobertura de testes para services e endpoints críticos.
- Padronizar respostas JSON e versionamento definitivo dos endpoints.
- Implementar pipeline CI para lint/test/coverage.
- Migrar frontend legado (JS puro) para framework moderno (React/Vue) quando possível.
