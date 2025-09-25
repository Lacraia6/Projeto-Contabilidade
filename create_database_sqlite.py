import sys
sys.dont_write_bytecode = True
import sqlite3
from pathlib import Path

CAMINHO_DB = Path(__file__).parent.parent / "data_base.db"
DATA_BASE_COMMANDS = Path(__file__).parent.parent / "comandosSQL.sql"


def execute_command(command, value=None):
    conn = sqlite3.connect(CAMINHO_DB, timeout=30, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA busy_timeout = 5000;")

    cursor = conn.cursor()
    try:
        if value is None:
            cursor.execute(command)
        else:
            cursor.execute(command, value)
        if command.strip().upper().startswith("SELECT"):
            rows = cursor.fetchall()
            return [dict(row) for row in rows]  
        else:
            conn.commit()
            return cursor.lastrowid
    finally:
        cursor.close()
        conn.close()

def create_database():
    print("Verificando Banco de dados...")
    if not CAMINHO_DB.exists():
        print("Criando Banco de dados...")
        conn = sqlite3.connect(CAMINHO_DB, timeout=30, check_same_thread=False)
        cursor = conn.cursor()
        with open(DATA_BASE_COMMANDS, "r", encoding="utf-8") as f:
            sql_script = f.read()
        cursor.executescript(sql_script)   
        conn.commit()
        cursor.close()
        conn.close() 
        print("Banco de dados criado...")
        return