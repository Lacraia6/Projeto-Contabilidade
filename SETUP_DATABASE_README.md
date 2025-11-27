# Setup do Banco de Dados

## Como usar

Execute o script Python para configurar o banco de dados automaticamente:

```bash
python setup_database.py
```

## O que o script faz

1. Conecta ao MySQL
2. Cria o banco de dados `contabilidade` se nao existir
3. Executa o arquivo `init_database.sql`
4. Cria todas as tabelas
5. Insere os dados iniciais

## Requisitos

- Python 3.x
- PyMySQL instalado (ja esta no requirements.txt)
- MySQL rodando na porta 3306

## Credenciais configuradas

- Host: localhost:3306
- Usuario: root
- Senha: Gabrielrochadias12
- Banco: contabilidade

## Credenciais de acesso ao sistema

Apos executar o script, voce pode fazer login com:

- **Admin**: login='admin', senha='123'
- **Joao Silva**: login='joao.silva', senha='123'
- **Maria Santos**: login='maria.santos', senha='123'
- E outros usuarios...

## Troubleshooting

Se der erro de conexao:
- Verifique se o MySQL esta rodando
- Verifique se as credenciais estao corretas
- Verifique se a porta 3306 esta aberta

Se der erro de PyMySQL:
```bash
pip install pymysql
```


