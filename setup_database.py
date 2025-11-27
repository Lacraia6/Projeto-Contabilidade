#!/usr/bin/env python3
"""
Script para configurar o banco de dados
Executa o arquivo init_database.sql no MySQL
"""

import pymysql
import sys
import os
from pathlib import Path

# Configuracoes do banco de dados
DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': 'Gabrielrochadias12',
    'database': 'contabilidade',
    'charset': 'utf8mb4',
    'autocommit': False
}

SQL_FILE = 'init_database.sql'


def read_sql_file(file_path):
    """Le o arquivo SQL e retorna o conteudo"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"ERRO: Arquivo {file_path} nao encontrado!")
        sys.exit(1)
    except Exception as e:
        print(f"ERRO ao ler arquivo SQL: {e}")
        sys.exit(1)


def execute_sql_script(connection, sql_content):
    """Executa o script SQL"""
    try:
        cursor = connection.cursor()
        
        # Divide o script em comandos individuais
        # Remove linhas vazias e separa por ponto e virgula
        commands = []
        current_command = []
        
        for line in sql_content.split('\n'):
            line = line.strip()
            if not line or line.startswith('--'):
                continue
            
            current_command.append(line)
            
            if line.endswith(';'):
                command = ' '.join(current_command)
                if command.strip():
                    commands.append(command)
                current_command = []
        
        # Executa cada comando
        print(f"Executando {len(commands)} comandos SQL...")
        
        for i, command in enumerate(commands, 1):
            try:
                cursor.execute(command)
                if i % 10 == 0:
                    print(f"  Executado {i}/{len(commands)} comandos...")
            except Exception as e:
                print(f"\nERRO no comando {i}:")
                print(f"Comando: {command[:100]}...")
                print(f"Erro: {e}")
                connection.rollback()
                raise
        
        connection.commit()
        print(f"\n✓ Todos os {len(commands)} comandos executados com sucesso!")
        return True
        
    except Exception as e:
        print(f"\nERRO ao executar script SQL: {e}")
        connection.rollback()
        return False
    finally:
        cursor.close()


def create_database_if_not_exists(connection):
    """Cria o banco de dados se nao existir"""
    try:
        cursor = connection.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        cursor.execute(f"USE {DB_CONFIG['database']}")
        connection.commit()
        cursor.close()
        print(f"✓ Banco de dados '{DB_CONFIG['database']}' verificado/criado com sucesso!")
        return True
    except Exception as e:
        print(f"ERRO ao criar banco de dados: {e}")
        return False


def main():
    """Funcao principal"""
    print("=" * 60)
    print("SCRIPT DE CONFIGURACAO DO BANCO DE DADOS")
    print("=" * 60)
    print(f"\nConfiguracoes:")
    print(f"  Host: {DB_CONFIG['host']}:{DB_CONFIG['port']}")
    print(f"  Usuario: {DB_CONFIG['user']}")
    print(f"  Banco: {DB_CONFIG['database']}")
    print(f"  Arquivo SQL: {SQL_FILE}")
    print()
    
    # Verifica se o arquivo SQL existe
    if not os.path.exists(SQL_FILE):
        print(f"ERRO: Arquivo {SQL_FILE} nao encontrado!")
        print(f"Certifique-se de que o arquivo esta no diretorio atual.")
        sys.exit(1)
    
    # Conecta ao MySQL (sem especificar database primeiro)
    try:
        print("Conectando ao MySQL...")
        connection = pymysql.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            charset=DB_CONFIG['charset']
        )
        print("✓ Conectado ao MySQL com sucesso!")
        
    except Exception as e:
        print(f"ERRO ao conectar ao MySQL: {e}")
        print("\nVerifique:")
        print("  - Se o MySQL esta rodando")
        print("  - Se as credenciais estao corretas")
        print("  - Se o PyMySQL esta instalado (pip install pymysql)")
        sys.exit(1)
    
    try:
        # Cria o banco de dados se nao existir
        if not create_database_if_not_exists(connection):
            sys.exit(1)
        
        # Reconecta ao banco especifico
        connection.close()
        connection = pymysql.connect(**DB_CONFIG)
        print(f"✓ Conectado ao banco '{DB_CONFIG['database']}'!")
        
        # Le o arquivo SQL
        print(f"\nLendo arquivo {SQL_FILE}...")
        sql_content = read_sql_file(SQL_FILE)
        print(f"✓ Arquivo lido com sucesso! ({len(sql_content)} caracteres)")
        
        # Executa o script
        print(f"\nExecutando script SQL...")
        if execute_sql_script(connection, sql_content):
            print("\n" + "=" * 60)
            print("✓ BANCO DE DADOS CONFIGURADO COM SUCESSO!")
            print("=" * 60)
            print("\nCredenciais de acesso:")
            print("  Admin: login='admin', senha='123'")
            print("  Outros usuarios: login='joao.silva', senha='123'")
            print("                     login='maria.santos', senha='123'")
            print("                     etc.")
            print("\nPronto para usar!")
        else:
            print("\n" + "=" * 60)
            print("ERRO: Falha ao configurar o banco de dados")
            print("=" * 60)
            sys.exit(1)
            
    except Exception as e:
        print(f"\nERRO inesperado: {e}")
        sys.exit(1)
    finally:
        connection.close()
        print("\nConexao fechada.")


if __name__ == '__main__':
    main()

